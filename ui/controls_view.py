"""Componente per la gestione e il rendering dei controlli utente e delle opzioni."""
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
    PREZZI_FILE,
    clear_all_caches,
    fonte_download,
    leggi_brent_score,
    get_mimit_dataset,
    candidati,
    impronta,
    load_data,
    brent_yahoo,
)
from ui.formatters import _it, num
from ui.hero_view import render_error
from ui.preferenze import OPZIONI, valore

HOME, FAQ = "Home", "F.A.Q."
# capacità del serbatoio e consumo ogni 100 km predefiniti, nell'unità del carburante (kg per il Metano)
PREDEFINITI = {"Benzina": (50.0, 5.0), "Gasolio": (50.0, 5.0), "GPL": (40.0, 7.0), "Metano": (14.0, 4.0)}


def _vai(scheda: str) -> None:
    st.session_state["scheda"] = scheda


def _pillola(col, scheda: str, key: str) -> None:
    """Pulsante a pillola che apre una scheda; quella aperta è in blu scuro (type="primary")."""
    aperta = st.session_state.get("scheda", HOME) == scheda
    col.button(scheda, key=key, type="primary" if aperta else "secondary", on_click=_vai, args=(scheda,),
               width="stretch")


@dataclass
class ControlsResult:
    origin: tuple[float, float]
    params: fm.ModelParams
    cands: pd.DataFrame
    fonte: str
    note_dati: Sequence[str]
    raggio: int | float
    unita: str  # «l» o «kg» (Metano): unità del prezzo e del serbatoio
    ref_mode: str
    show_all_lines: bool
    hero_testo: any  # colonna del testo nel riquadro «Consiglio»
    hero_cerchio: any  # posto del cerchio dello score, a destra nel riquadro «Consiglio»
    contenuto: any  # dentro il riquadro delle schede, sotto la riga dei comandi
    nota_posizione: str  # «Perugia (stima)» / «Roma (ripiego)» se non viene dal GPS, altrimenti ""
    top5: any  # riquadro apribile «Top 5» nella riga dei comandi
    metriche: any  # posto degli indicatori della Home, accanto al menu del carburante (None nelle altre schede)
    bs: dict | None  # score del petrolio (None se manca)
    bs_err: str  # perché manca lo score
    esclusi: int = 0  # distributori tolti perché le coordinate non tornano con il loro comune
    caricamento: any = None  # il cerchio di caricamento, da chiudere a pagina completa


class ControlsView:
    @staticmethod
    def render(c_hero: any, posizione: tuple[tuple[float, float] | None, str]) -> ControlsResult:
        """`posizione` = rileva_posizione(), chiesta in cima ad app.py (GPS, o indirizzo internet se fallisce)."""
        up_a = st.session_state.get("up_anag")
        up_p = st.session_state.get("up_prezzi")

        # un solo cerchio di caricamento al centro dello schermo: dati MIMIT (fino al 60%), lettura dei CSV,
        # Brent, score del petrolio e posizione; si chiude in fondo ad app.py, a pagina completa
        caricamento = style.Caricamento()
        st.session_state.pop("download_err", None)
        (anag_b, src_a), (prezzi_b, src_p) = get_mimit_dataset(
            lambda pct, testo: caricamento.mostra(pct * 60 // 100, testo), up_a, up_p)

        if anag_b is None or prezzi_b is None:
            caricamento.chiudi()
            errori = "<br>".join(escape(e) for e in st.session_state.get("download_err", []))
            render_error(c_hero, "Non sono riuscito a scaricare i dati dal sito del MIMIT"
                         + (f":<br><code>{errori}</code><br>" if errori else ". ")
                         + f"Riprova più tardi, oppure carica i due CSV (<code>{ANAG_FILE}</code> e <code>{PREZZI_FILE}</code>) "
                           "da «Opzioni» qui sotto, o mettili nella cartella <code>data/</code> accanto ad "
                           "<code>app.py</code>.")
            c_controls = style.card("controls")
            with c_controls:
                adv = st.expander("Opzioni", expanded=True)
                with adv:
                    style.section("Dati")
                    st.file_uploader("Anagrafica impianti (CSV)", type="csv", help=ANAG_FILE, key="up_anag")
                    st.file_uploader("Prezzi alle 8 (CSV)", type="csv", help=PREZZI_FILE, key="up_prezzi")
            style.colophon()
            st.stop()

        caricamento.mostra(65, "Leggo i prezzi dei distributori…")
        anag, prezzi, extraction = load_data(anag_b, prezzi_b)
        if anag.empty or prezzi.empty:
            caricamento.chiudi()
            render_error(c_hero, "Uno dei CSV non contiene righe valide: controlla di aver caricato i file giusti.")
            style.colophon()
            st.stop()

        caricamento.mostra(75, "Leggo il prezzo del petrolio…")
        brent, brent_err = brent_yahoo(BRENT_GIORNI)
        caricamento.mostra(85, "Leggo lo score del petrolio…")
        bs, bs_err = leggi_brent_score()
        if brent:
            dB = fm.brent_delta(brent["b_t"], brent["b_tn"], brent["fx_t"], brent["fx_tn"])
            db_txt = _it(f"{dB:+.2%}")
            nota_brent = (f"Brent {num(brent['b_tn'], 2)} → {num(brent['b_t'], 2)} $/bbl "
                          f"({brent['data_tn']:%d/%m} → {brent['data_t']:%d/%m}, Yahoo Finance) · variazione {db_txt}")
        else:
            dB = 0.0
            nota_brent = f"Brent non disponibile da Yahoo Finance ({escape(brent_err)}): non considerato"

        # riquadro «Consiglio»: testo a sinistra; a destra il cerchio dello score
        hero_testo, hero_lato = style.hero_box(c_hero)
        with hero_lato:
            hero_cerchio = st.container()

        # riquadro delle schede: in cima la riga Home · Posizione · Opzioni · Top 5 · F.A.Q., sotto il contenuto
        st.session_state.setdefault("scheda", HOME)
        with style.card("schede"):
            with st.container(key="comandi"):
                col_home, col_pos, col_adv, col_top, col_faq = st.columns(5, gap="small", vertical_alignment="top")
            contenuto = st.container()

        # Home: in cima la riga degli indicatori, con il menu del carburante accanto a «Costo al km» (gli indicatori
        # li scrive ResultView). Nelle altre schede il menu non c'è e vale il carburante già scelto.
        metriche = None
        # il menu del carburante c'è solo nella Home: la scelta vive in «_carburante» (scritta anche dal pulsante
        # d'avvio), così resta nelle altre schede; all'inizio vale quella salvata nel browser
        carburante = st.session_state.get("_carburante") or valore("carburante", fm.FUELS[0])
        if st.session_state.get("scheda", HOME) == HOME:
            with contenuto:
                with st.container(key="metriche"):
                    metriche, col_carb = st.columns([3, 1], gap="small")
            with col_carb:
                with st.container(key="carb"):
                    style.html('<div class="x-label">Carburante</div>')
                    fuel = st.selectbox("Carburante", fm.FUELS, label_visibility="collapsed", key="carburante",
                                        index=fm.FUELS.index(carburante))
        else:
            fuel = carburante
        st.session_state["_carburante"] = fuel

        _pillola(col_home, HOME, "nav_home")
        _pillola(col_faq, FAQ, "nav_faq")
        with col_pos:
            if st.button("Posizione", help="Rileva di nuovo la posizione dal browser", width="stretch"):
                st.session_state["geo_giro"] = st.session_state.get("geo_giro", 0) + 1
                st.rerun()

        # «Opzioni» e «Top 5» si aprono come popover sopra la pagina (restano aperti mentre si cambiano i valori)
        with col_adv:
            adv = st.popover("Opzioni", width="stretch")
            adv_pos, adv_model, adv_data = adv.container(), adv.container(), adv.container()
        top5 = col_top.popover("Top 5", width="stretch")  # si riempie in app.py, dopo il calcolo

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
            if fonte_download():
                nota_prezzi += f" {fonte_download()}"
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

        caricamento.mostra(95, "Cerco la tua posizione…")
        # nota_posizione: riga nel riquadro «Consiglio» quando la posizione non è quella del GPS
        origin, nota_posizione = posizione
        if comune_override:
            sel = anag[anag.comune == comune_override]
            origin, nota_posizione = (float(sel.lat.median()), float(sel.lon.median())), ""

        if origin is None:  # il browser non ha ancora risposto (al massimo 15 secondi): il cerchio resta al centro
            # subito, senza ritardo: la pagina si ferma qui e sotto il resto sparisce
            caricamento.mostra(95, "Cerco la tua posizione…", subito=True)
            top5.caption("Serve la posizione per trovare i distributori migliori.")
            style.colophon()
            st.stop()
        # il cerchio resta aperto: si chiude in fondo ad app.py, a pagina completa (dopo le distanze su strada)

        u = fm.unita(fuel)
        unita_lunga = "kg" if u == "kg" else "litri"
        v_tot_0, consumo_0 = PREDEFINITI.get(fuel, (50.0, 5.0))
        # valore iniziale di ogni opzione: quello salvato nel browser alla visita precedente, o il predefinito
        def iniziale(chiave: str, predefinito=None):
            return valore(chiave, OPZIONI[chiave][0] if predefinito is None else predefinito)

        with adv_model:
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                # una chiave per carburante: cambiando carburante tornano i suoi valori predefiniti
                v_tot = st.number_input(f"Capacità del serbatoio ({unita_lunga})", min_value=5.0, max_value=200.0,
                                        value=iniziale(f"v_tot_{fuel}", v_tot_0), step=1.0, key=f"v_tot_{fuel}")
                livello = st.slider("Carburante nel serbatoio (%)", 0, 100, 25, 1) / 100
                consumo = st.number_input(f"Consumo ({u}/100 km)", min_value=1.0, max_value=40.0,
                                          value=iniziale(f"consumo_{fuel}", consumo_0), step=0.1, key=f"consumo_{fuel}")
                raggio = st.slider("Raggio d'azione (km su strada)", 2, 60, iniziale("opt_raggio"), key="opt_raggio")
                livello_min = st.slider("Soglia di riserva (%)", 0, 50, iniziale("opt_riserva"), 1, key="opt_riserva",
                                        help="Sotto questo livello conviene sempre fare rifornimento.") / 100
                litri = None
                if st.checkbox(f"Scegli quanti {unita_lunga} fare (altrimenti il pieno)"):
                    litri = st.number_input(f"{unita_lunga.capitalize()} da fare", min_value=1.0, max_value=float(v_tot),
                                            value=min(30.0, float(v_tot)), step=1.0, key=f"litri_{fuel}")
            with col_v2:
                senza_self = fuel in fm.SENZA_SELF
                self_service = st.radio(
                    "Self o servito", ["Self", "Servito"], horizontal=True, disabled=senza_self, key="opt_self",
                    index=["Self", "Servito"].index(iniziale("opt_self")),
                    help="Per GPL e Metano non conta: quasi tutti li vendono solo serviti, quindi si usa il prezzo "
                         "che c'è (se ci sono entrambi, il più basso).") == "Self"
                use_osrm = st.checkbox("Calcola percorsi reali (OSRM)", value=iniziale("opt_osrm"), key="opt_osrm",
                                       help="Usa l'API pubblica di OSRM per distanze reali invece della linea d'aria.")
                show_all_lines = st.checkbox("Mostra linea d'aria verso tutti i distributori sulla mappa",
                                             value=iniziale("opt_linee"), key="opt_linee")
                usura = st.number_input("Usura dell'auto (€/km)", min_value=0.0, max_value=1.0, step=0.01,
                                        value=iniziale("opt_usura"), format="%.3f", key="opt_usura")
                valore_tempo = st.number_input(
                    "Valore del tuo tempo (€/ora)", min_value=0.0, max_value=100.0, step=1.0, key="opt_tempo",
                    value=iniziale("opt_tempo"),
                    help="Il tempo per andare al distributore e tornare conta come un costo: un distributore lontano "
                         "deve far risparmiare di più. 0 = conta solo carburante e usura.")
                autostrade = st.checkbox(
                    "Includi i distributori in autostrada", value=iniziale("opt_autostrade"), key="opt_autostrade",
                    help="Di solito costano di più e si raggiungono solo dall'autostrada, a volte in una sola "
                         "direzione: la distanza calcolata può non essere quella vera.")
                max_age = st.number_input("Età massima del prezzo (giorni)", min_value=1, max_value=60, key="opt_eta",
                                          value=iniziale("opt_eta"),
                                          help="I prezzi comunicati da più giorni possono essere cambiati. Con 5 "
                                               "giorni restano circa 95 distributori su 100.")
                road_factor = st.slider("Strada in più rispetto alla linea d'aria (×)", 1.0, 2.0, iniziale("opt_strada"), 0.05, key="opt_strada",
                                        help="1,3 = la strada è in media il 30% più lunga della distanza in linea d'aria.")
                ref_mode = st.radio("Prezzo tipico della zona", ["mediana", "media"], horizontal=True, key="opt_rif",
                                    index=["mediana", "media"].index(iniziale("opt_rif")),
                                    help="Mediana: il prezzo di mezzo, non risente dei prezzi anomali. Media: la media semplice.")
                theta = st.number_input("Soglia di convenienza (€)", min_value=-1000.0, max_value=1000.0, step=0.5,
                                        value=iniziale("opt_soglia"), key="opt_soglia",
                                        help="Il verdetto è «Rifornisci» solo se il risparmio rispetto al "
                                             "distributore più vicino supera questa cifra.")
                alpha = st.slider("Peso del petrolio sui prezzi (%)", 0, 40, iniziale("opt_alpha"), 1, key="opt_alpha",
                                  help="Quota della variazione del Brent che si trasferisce sui prezzi alla pompa.") / 100

        params = fm.ModelParams(
            v_tot=v_tot, livello=livello, litri=litri, alpha=alpha, delta_brent=dB,
            consumo_l100=consumo, usura_eur_km=usura, road_factor=road_factor, raggio_km=float(raggio),
            use_osrm=use_osrm, ref_mode=ref_mode, theta=theta, livello_min=livello_min,
            valore_tempo=valore_tempo, autostrade=autostrade,
        )
        cands = candidati(anag, prezzi, impronta(anag_b, prezzi_b), fuel, self_service, float(max_age), extraction)

        data_estrazione = f"{extraction:%d/%m/%Y}" if extraction is not None else "data sconosciuta"
        fonte = (f"Estrazione MIMIT del {data_estrazione} · {len(cands):,} distributori con prezzo "
                 f"{fuel} {'self o servito' if senza_self else 'self' if self_service else 'servito'} valido in "
                 "tutta Italia").replace(",", ".")

        return ControlsResult(
            origin=origin,
            params=params,
            cands=cands,
            fonte=fonte,
            note_dati=note_dati,
            raggio=raggio,
            unita=u,
            ref_mode=ref_mode,
            show_all_lines=show_all_lines,
            hero_testo=hero_testo,
            hero_cerchio=hero_cerchio,
            contenuto=contenuto,
            nota_posizione=nota_posizione,
            top5=top5,
            metriche=metriche,
            bs=bs,
            bs_err=bs_err,
            esclusi=anag.attrs.get("esclusi", 0),
            caricamento=caricamento,
        )
