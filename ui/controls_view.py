"""Componente per la gestione e il rendering dei controlli utente e delle opzioni avanzate."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Sequence

import pandas as pd
import streamlit as st

import fuel_model as fm
import style
from ui.data_service import (
    ANAG_FILE,
    BRENT_GIORNI,
    CACHE_ORE,
    PREZZI_FILE,
    clear_all_caches,
    get_bytes,
    get_mimit_dataset,
    load_data,
    brent_yahoo,
    posizione_browser,
)
from ui.formatters import _it, num
from ui.hero_view import render_error, render_waiting


@dataclass
class ControlsResult:
    origin: tuple[float, float]
    fuel: str
    params: fm.ModelParams
    cands: pd.DataFrame
    fonte: str
    note_dati: Sequence[str]
    raggio: int | float
    litri: float | None
    ref_mode: str
    show_all_lines: bool


class ControlsView:
    @staticmethod
    def render(c_hero: any) -> ControlsResult:
        up_a = st.session_state.get("up_anag")
        up_p = st.session_state.get("up_prezzi")

        c_progress = st.empty()
        st.session_state.pop("download_err", None)
        (anag_b, src_a), (prezzi_b, src_p) = get_mimit_dataset(c_progress, up_a, up_p)
        c_progress.empty()

        if anag_b is None or prezzi_b is None:
            errori = "<br>".join(escape(e) for e in st.session_state.get("download_err", []))
            render_error(c_hero, "Non sono riuscito a scaricare i dati dal sito del MIMIT"
                         + (f":<br><code>{errori}</code><br>" if errori else ". ")
                         + f"Riprova più tardi, oppure carica i due CSV (<code>{ANAG_FILE}</code> e <code>{PREZZI_FILE}</code>) "
                           "da «Opzioni avanzate» qui sotto, o mettili nella cartella <code>data/</code> accanto ad "
                           "<code>app.py</code>.")
            c_controls = style.card("controls")
            with c_controls:
                adv = st.expander("Opzioni avanzate", expanded=True)
                with adv:
                    style.section("Dati")
                    st.file_uploader("Anagrafica impianti (CSV)", type="csv", help=ANAG_FILE, key="up_anag")
                    st.file_uploader("Prezzi alle 8 (CSV)", type="csv", help=PREZZI_FILE, key="up_prezzi")
            style.colophon()
            st.stop()

        anag, prezzi, extraction = load_data(anag_b, prezzi_b)
        if anag.empty or prezzi.empty:
            render_error(c_hero, "Uno dei CSV non contiene righe valide: controlla di aver caricato i file giusti.")
            style.colophon()
            st.stop()

        brent, brent_err = brent_yahoo(BRENT_GIORNI)
        if brent:
            dB = fm.brent_delta(brent["b_t"], brent["b_tn"], brent["fx_t"], brent["fx_tn"])
            db_txt = _it(f"{dB:+.2%}")
            nota_brent = (f"Brent {num(brent['b_tn'], 2)} → {num(brent['b_t'], 2)} $/bbl "
                          f"({brent['data_tn']:%d/%m} → {brent['data_t']:%d/%m}, Yahoo Finance) · variazione {db_txt}")
        else:
            dB = 0.0
            nota_brent = f"Brent non disponibile da Yahoo Finance ({escape(brent_err)}): non considerato"

        c_controls = style.card("controls")
        with c_controls:
            c_row = st.container()
            adv = st.expander("Opzioni avanzate")
            adv_pos, adv_model, adv_data = adv.container(), adv.container(), adv.container()

        with adv_data:
            style.section("Dati")
            st.file_uploader("Anagrafica impianti (CSV)", type="csv", help=ANAG_FILE, key="up_anag")
            st.file_uploader("Prezzi alle 8 (CSV)", type="csv", help=PREZZI_FILE, key="up_prezzi")
            st.caption("I prezzi MIMIT si aggiornano ogni mattina alle 09:00. "
                       "I CSV caricati qui hanno la precedenza.")
            if st.button("Riscarica ora", width="stretch", help="Scarica di nuovo prezzi MIMIT e Brent."):
                clear_all_caches()
                st.rerun()

        del_giorno = f" del {extraction:%d/%m/%Y}" if extraction is not None else ""
        if "caricato" in (src_a, src_p):
            nota_prezzi = f"Prezzi MIMIT{del_giorno} da file caricati a mano"
        elif "locale" in (src_a, src_p):
            nota_prezzi = f"Prezzi MIMIT{del_giorno} dalla cartella data/"
        else:
            quando = st.session_state["scaricato_alle"]
            nota_prezzi = f"Prezzi MIMIT{del_giorno}, scaricati alle {quando:%H:%M} del {quando:%d/%m}"
        if extraction is None:
            nota_prezzi += " (data di estrazione non trovata: filtro sull'età del prezzo disattivato)"
        note_dati = [escape(nota_prezzi), nota_brent]

        with adv_pos:
            comuni = sorted(anag.comune.unique())
            comune_override = st.selectbox(
                "Comune (in alternativa al GPS)",
                comuni,
                index=None,
                placeholder="Scegli un comune se il GPS è disattivato…",
                key="comune_fallback",
            )

        origin, nota = posizione_browser()
        if comune_override:
            sel = anag[anag.comune == comune_override]
            origin = (float(sel.lat.median()), float(sel.lon.median()))
            nota = f"Posizione impostata su {comune_override} (da Opzioni avanzate)"

        with c_row:
            col_pos, col_fuel = st.columns([1, 1], gap="medium", vertical_alignment="center")
            with col_pos:
                if st.button("Aggiorna posizione", width="stretch"):
                    st.session_state["geo_giro"] = st.session_state.get("geo_giro", 0) + 1
                    st.rerun()
            with col_fuel:
                fuel = st.selectbox("Prodotto", fm.FUELS, label_visibility="collapsed")

        if origin is None:
            render_waiting(c_hero, nota)
            style.colophon()
            st.stop()

        with adv_model:
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                v_tot = st.number_input("Capacità del serbatoio (litri)", min_value=5.0, max_value=200.0, value=50.0, step=1.0)
                livello = st.slider("Carburante nel serbatoio (%)", 0, 100, 25, 1) / 100
                consumo = st.number_input("Consumo (l/100 km)", min_value=1.0, max_value=40.0, value=5.0, step=0.1)
                raggio = st.slider("Raggio d'azione (km su strada)", 2, 60, 20)
                livello_min = st.slider("Soglia di riserva (%)", 0, 50, 10, 1,
                                        help="Sotto questo livello conviene sempre fare rifornimento.") / 100
                litri = None
                if st.checkbox("Scegli quanti litri fare (altrimenti il pieno)"):
                    litri = st.number_input("Litri da fare", min_value=1.0, max_value=float(v_tot),
                                            value=min(30.0, float(v_tot)), step=1.0)
            with col_v2:
                self_service = st.radio("Self o servito", ["Self", "Servito"], horizontal=True) == "Self"
                use_osrm = st.checkbox("Calcola percorsi reali (OSRM)", value=True, help="Usa l'API pubblica di OSRM per distanze reali invece della linea d'aria.")
                show_all_lines = st.checkbox("Mostra linea d'aria verso tutti i distributori sulla mappa", value=False)
                usura = st.number_input("Usura dell'auto (€/km)", min_value=0.0, max_value=1.0, value=0.05, step=0.01,
                                        format="%.3f")
                max_age = st.number_input("Età massima del prezzo (giorni)", min_value=1, max_value=60, value=7)
                road_factor = st.slider("Strada in più rispetto alla linea d'aria (×)", 1.0, 2.0, 1.3, 0.05,
                                        help="1,3 = la strada è in media il 30% più lunga della distanza in linea d'aria.")
                ref_mode = st.radio("Prezzo tipico della zona", ["mediana", "media"], horizontal=True,
                                    help="Mediana: il prezzo di mezzo, non risente dei prezzi anomali. Media: la media semplice.")
                theta = st.number_input("Soglia di convenienza (€)", value=0.0, step=0.5,
                                        help="Il verdetto è «Rifornisci» solo se il risparmio supera questa cifra.")
                alpha = st.slider("Peso del petrolio sui prezzi (%)", 0, 40, 20, 1,
                                  help="Quota della variazione del Brent che si trasferisce sui prezzi alla pompa.") / 100

        params = fm.ModelParams(
            v_tot=v_tot, livello=livello, litri=litri, alpha=alpha, delta_brent=dB,
            consumo_l100=consumo, usura_eur_km=usura, road_factor=road_factor, raggio_km=float(raggio),
            use_osrm=use_osrm, ref_mode=ref_mode, theta=theta, livello_min=livello_min,
        )
        cands = fm.build_candidates(anag, prezzi, fuel, self_service, float(max_age), extraction)

        data_estrazione = f"{extraction:%d/%m/%Y}" if extraction is not None else "data sconosciuta"
        fonte = (f"Estrazione MIMIT del {data_estrazione} · {len(cands):,} distributori con prezzo "
                 f"{fuel} {'self' if self_service else 'servito'} valido in tutta Italia").replace(",", ".")

        return ControlsResult(
            origin=origin,
            fuel=fuel,
            params=params,
            cands=cands,
            fonte=fonte,
            note_dati=note_dati,
            raggio=raggio,
            litri=litri,
            ref_mode=ref_mode,
            show_all_lines=show_all_lines,
        )
