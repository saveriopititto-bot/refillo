"""App Streamlit: pesi degli archi (posizione -> distributori) con lo score di rifornimento."""
from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit_js_eval

import fuel_model as fm
import style
from ui.config import supabase_config
from ui.formatters import _it, eur, num
from ui.map_deck import build_fuel_deck

st.set_page_config(page_title="Conviene rifornire?", page_icon="⛽", layout="wide", initial_sidebar_state="collapsed")
style.apply_style()

BASE = Path(__file__).parent
ANAG_FILE, PREZZI_FILE = fm.ANAG_FILE, fm.PREZZI_FILE
CACHE_ORE = 3  # i prezzi MIMIT cambiano una volta al giorno
BRENT_GIORNI = 7  # n: finestra della variazione del Brent




# --------------------------------------------------------------------------
# Dati
# --------------------------------------------------------------------------
def default_path(name: str) -> Path | None:
    for d in (BASE / "data", BASE, Path.cwd()):
        if (d / name).exists():
            return d / name
    return None


@st.cache_data(max_entries=2, show_spinner="Leggo i CSV…")  # una copia per giorno di dati, non di più
def load_data(anag_bytes: bytes, prezzi_bytes: bytes):
    anag, extraction = fm.parse_anagrafica(anag_bytes)
    prezzi = fm.parse_prezzi(prezzi_bytes)
    return anag, prezzi, extraction


@st.cache_data(ttl=CACHE_ORE * 3600, show_spinner="Scarico i dati aggiornati dal MIMIT…")
def download(name: str) -> tuple[bytes, pd.Timestamp]:
    return fm.download_csv(name), pd.Timestamp.now(tz="Europe/Rome")


@st.cache_data(ttl=CACHE_ORE * 3600, show_spinner="Scarico il Brent da Yahoo Finance…")
def brent_yahoo(n_giorni: int) -> tuple[dict | None, str]:
    """Brent ed EUR/USD da Yahoo Finance; in caso di errore (None, motivo), così anche il fallimento resta in cache."""
    try:
        return fm.fetch_brent_yf(n_giorni), ""
    except Exception as e:  # rete assente, Yahoo non risponde, dati insufficienti
        return None, str(e) or type(e).__name__




@st.cache_data(ttl=CACHE_ORE * 3600, show_spinner="Leggo lo score del petrolio…")
def brent_score(url: str, chiave: str) -> tuple[dict | None, str]:
    """Ultimo score del Brent da Supabase; (None, motivo) se non raggiungibile. Anche l'errore resta in cache."""
    try:
        return fm.fetch_brent_score(url, chiave), ""
    except Exception as e:  # rete assente, tabella vuota, chiave sbagliata
        return None, str(e) or type(e).__name__




PERCHE_PETROLIO = {
    1: "Il petrolio costa più del solito. Tra pochi giorni anche il carburante costerà di più. Fai il pieno oggi.",
    0: "Il petrolio costa come al solito. La benzina non cambierà molto. Fai benzina quando ti serve.",
    -1: "Il petrolio costa meno del solito. Tra pochi giorni anche la benzina costerà di meno. Se puoi, aspetta.",
}


def perche_petrolio(bs: dict) -> str:
    """Il perché del consiglio (HTML sicuro)."""
    return escape(PERCHE_PETROLIO[bs["esito"]])


def leggi_brent_score() -> tuple[dict | None, str]:
    """Score del petrolio, oppure (None, motivo). «Non configurato» non va in cache: appena si aggiungono i
    Secrets, l'app li trova."""
    url, chiave, nomi = supabase_config()
    if not (url and chiave):
        mancano = [n for n, v in (("SUPABASE_URL", url), ("SUPABASE_ANON_KEY", chiave)) if not v]
        trovati = ", ".join(nomi) if nomi else "nessuno"
        return None, f"non configurato|{', '.join(mancano)}|{trovati}"
    return brent_score(url, chiave)


def nota_score(motivo: str) -> str:
    """Riga (HTML sicuro) che spiega perché manca lo score del petrolio e il «Consiglio» usa il verdetto sul risparmio."""
    if motivo.startswith("non configurato|"):
        _, mancano, trovati = motivo.split("|", 2)
        return (f"Score del petrolio non configurato: nei Secrets di questa app su Streamlit manca "
                f"<code>{escape(mancano)}</code> (segreti trovati: <code>{escape(trovati)}</code>)")
    return f"Score del petrolio da Supabase non raggiungibile ({escape(motivo)})"


def get_bytes(uploaded, name: str) -> tuple[bytes | None, str]:
    """Contenuto del CSV e da dove arriva: caricato a mano, cartella data/ o download dal MIMIT."""
    if uploaded is not None:
        return uploaded.getvalue(), "caricato"
    p = default_path(name)
    if p:
        return p.read_bytes(), "locale"
    try:
        data, quando = download(name)
    except Exception as e:  # rete assente, sito MIMIT giù, risposta non valida
        st.session_state.setdefault("download_err", []).append(f"{name}: {e}")
        return None, ""
    st.session_state["scaricato_alle"] = quando
    return data, "scaricato"


GEO_ERRORI = {
    1: "hai negato il permesso di accedere alla posizione (puoi riattivarlo dalle impostazioni del sito nel browser)",
    2: "il dispositivo non riesce a determinare la posizione",
    3: "la richiesta di posizione è scaduta",
}


def posizione_browser() -> tuple[tuple[float, float] | None, str]:
    """Posizione reale dal browser (API Geolocation): ((lat, lon), nota) oppure (None, motivo)."""
    giro = st.session_state.get("geo_giro", 0)
    geo = streamlit_js_eval.get_geolocation(component_key=f"geo_{giro}")
    if not geo:
        return None, "Consenti l'accesso alla posizione quando il browser lo chiede…"
    if not isinstance(geo, dict):
        return None, "Posizione non disponibile."
    if "error" in geo:
        err = geo["error"] or {}
        msg = err.get("message", "errore sconosciuto") if isinstance(err, dict) else str(err)
        code = err.get("code") if isinstance(err, dict) else None
        return None, "Posizione non disponibile: " + GEO_ERRORI.get(code, msg) + "."
    c = geo.get("coords")
    if not c or not isinstance(c, dict):
        return None, "Posizione non disponibile."
    lat, lon = float(c["latitude"]), float(c["longitude"])
    acc = c.get("accuracy")
    nota = f"Posizione rilevata: {lat:.5f}, {lon:.5f}" + (f" (precisione ±{num(acc, 0)} m)" if acc else "")
    la0, la1, lo0, lo1 = fm.ITALY_BBOX
    if not (la0 <= lat <= la1 and lo0 <= lon <= lo1):
        nota += ". Sei fuori dall'Italia: i dati MIMIT coprono solo i distributori italiani."
    return (lat, lon), nota


def stop_with(msg: str) -> None:
    style.html(f'<div class="x-lead-box"><strong>⛽ Score di rifornimento</strong><br>{msg}</div>')
    style.colophon()
    st.stop()
# Controlli e dati
# --------------------------------------------------------------------------
c_hero = st.container()
c_controls = style.card("controls")
with c_controls:
    col_pos, col_fuel = st.columns([1, 1], gap="large")
    with col_pos:
        c_pos = st.container()
    with col_fuel:
        c_fuel = st.container()
        adv = st.expander("Opzioni avanzate")
        adv_model, adv_data = adv.container(), adv.container()

with adv_data:
    style.section("Dati")
    up_a = st.file_uploader("Anagrafica impianti (CSV)", type="csv", help=ANAG_FILE)
    up_p = st.file_uploader("Prezzi alle 8 (CSV)", type="csv", help=PREZZI_FILE)

st.session_state.pop("download_err", None)
(anag_b, src_a), (prezzi_b, src_p) = get_bytes(up_a, ANAG_FILE), get_bytes(up_p, PREZZI_FILE)

brent, brent_err = brent_yahoo(BRENT_GIORNI)
if brent:
    dB = fm.brent_delta(brent["b_t"], brent["b_tn"], brent["fx_t"], brent["fx_tn"])
    db_txt = _it(f"{dB:+.2%}")
    nota_brent = (f"Brent {num(brent['b_tn'], 2)} → {num(brent['b_t'], 2)} $/bbl "
                  f"({brent['data_tn']:%d/%m} → {brent['data_t']:%d/%m}, Yahoo Finance) · variazione {db_txt}")
else:
    dB = 0.0
    nota_brent = f"Brent non disponibile da Yahoo Finance ({escape(brent_err)}): non considerato"

with adv_data:
    st.caption(f"Prezzi MIMIT e Brent si scaricano da soli e si aggiornano ogni {CACHE_ORE} ore. "
               "I CSV caricati qui hanno la precedenza.")
    if st.button("Riscarica ora", width="stretch", help="Scarica di nuovo prezzi MIMIT e Brent."):
        download.clear()
        brent_yahoo.clear()
        brent_score.clear()
        st.rerun()

if anag_b is None or prezzi_b is None:
    errori = "<br>".join(escape(e) for e in st.session_state.get("download_err", []))
    with c_hero:
        style.error_card("Non sono riuscito a scaricare i dati dal sito del MIMIT"
                         + (f":<br><code>{errori}</code><br>" if errori else ". ")
                         + f"Riprova più tardi, oppure carica i due CSV (<code>{ANAG_FILE}</code> e <code>{PREZZI_FILE}</code>) "
                           "da «Opzioni avanzate» qui sotto, o mettili nella cartella <code>data/</code> accanto ad "
                           "<code>app.py</code>.")
    style.colophon()
    st.stop()

anag, prezzi, extraction = load_data(anag_b, prezzi_b)
if anag.empty or prezzi.empty:
    with c_hero:
        style.error_card("Uno dei CSV non contiene righe valide: controlla di aver caricato i file giusti.")
    style.colophon()
    st.stop()

# righe (HTML già sicuro) sui dati usati, mostrate nel riquadro del consiglio
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

with c_pos:
    style.section("1 · Dove sei")
    modo_pos = st.radio("Imposta da", ["La mia posizione", "Comune"], horizontal=True,
                        label_visibility="collapsed")
    origin, attesa_pos = None, ""
    if modo_pos == "La mia posizione":
        origin, nota = posizione_browser()
        attesa_pos = nota if origin is None else ""
        st.caption(nota)
        if st.button("Aggiorna posizione", width="stretch"):
            st.session_state["geo_giro"] = st.session_state.get("geo_giro", 0) + 1
            st.rerun()
    else:
        comuni = sorted(anag.comune.unique())
        idx = comuni.index("GUALDO TADINO") if "GUALDO TADINO" in comuni else 0
        comune = st.selectbox("Comune", comuni, index=idx)
        sel = anag[anag.comune == comune]
        origin = (float(sel.lat.median()), float(sel.lon.median()))
        st.caption(f"Centro stimato dai distributori del comune: {origin[0]:.5f}, {origin[1]:.5f}")

with c_fuel:
    style.section("2 · Carburante")
    fuel = st.selectbox("Prodotto", fm.FUELS, label_visibility="collapsed")

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

# --------------------------------------------------------------------------
# Calcolo
# --------------------------------------------------------------------------
if origin is None:
    with c_hero:
        style.html(f'<div class="x-lead-box"><strong>⛽ Score di rifornimento</strong><br>'
                   f'{escape(attesa_pos)}<br>In alternativa scegli <strong>Comune</strong> '
                   f'in «1 · Dove sei» qui sotto.</div>')
    style.colophon()
    st.stop()
params = fm.ModelParams(
    v_tot=v_tot, livello=livello, litri=litri, alpha=alpha, delta_brent=dB,
    consumo_l100=consumo, usura_eur_km=usura, road_factor=road_factor, raggio_km=float(raggio),
    use_osrm=use_osrm, ref_mode=ref_mode, theta=theta, livello_min=livello_min,
)
cands = fm.build_candidates(anag, prezzi, fuel, self_service, float(max_age), extraction)

data_estrazione = f"{extraction:%d/%m/%Y}" if extraction is not None else "data sconosciuta"
fonte = (f"Estrazione MIMIT del {data_estrazione} · {len(cands):,} distributori con prezzo "
         f"{fuel} {'self' if self_service else 'servito'} valido in tutta Italia").replace(",", ".")

edges, info = fm.compute_edges(cands, origin, params)
# score del petrolio dall'app «Prezzo del petrolio» (tabella brent_score in Supabase), per il riquadro «Consiglio»
bs, bs_err = leggi_brent_score()

# --------------------------------------------------------------------------
# Consiglio: in cima, sopra i controlli e le schede
# --------------------------------------------------------------------------
with c_hero:
    if edges.empty:
        style.error_card("Nessun distributore nel raggio scelto con un prezzo valido. "
                         "Aumenta il raggio o l'età massima del prezzo.")
        style.html(f'<p class="x-note">{"<br>".join(note_dati)}</p>')
    elif bs is not None and not info["riserva"]:  # il consiglio segue lo score del petrolio (sotto riserva no)
        titolo = fm.BRENT_SCORE_TESTI[bs["esito"]]
        style.hero("Consiglio", titolo, "", "", aside_html=style.cerchio_score(bs["esito"], "Petrolio: " + titolo),
                   nota_html=perche_petrolio(bs))
    else:
        corpo = escape(_it(info["motivo"][0].upper() + info["motivo"][1:])) + "."
        if not info["consiglio"]:
            corpo += " Il termine Brent è uguale per tutti i distributori: sposta lo score ma non cambia la classifica."
        style.hero("Consiglio", "Rifornisci" if info["consiglio"] else "Non conviene",
                   "", corpo, meta_html=note_dati + ([nota_score(bs_err)] if bs is None else []))

# Si disegna solo la scheda aperta: la mappa e la tabella degli archi non partono finché non servono.
tab_res, tab_arc, tab_how = st.tabs(["Risultato", "Archi", "Come funziona"], key="scheda", on_change="rerun")

# --------------------------------------------------------------------------
# Risultato
# --------------------------------------------------------------------------
if tab_res.open:
    with tab_res:
        if edges.empty:
            style.error_card("Nessun distributore da mostrare: nessun distributore nel raggio scelto.")
        else:
            best = info["best"]
            prezzo_txt = _it(f"{best.prezzo:.3f}") + " €/l"
            style.metrics([
                ("Prezzo di mercato", _it(f"{info['p_market']:.3f}") + " €/l",
                 f"{ref_mode} nel raggio"),
                ("Distributori", str(info["n"]), f"nel raggio di {raggio} km"),
                ("Litri da fare", num(info["q"]) + " l", "pieno" if litri is None else "impostati a mano"),
                ("Costo al km", _it(f"{info['c_km']:.3f}") + " €/km", "carburante + usura"),
            ])


            with style.card("map"):
                style.title("Dove conviene andare")
                style.lead(
                    f"Il distributore migliore è <strong>{escape(best.bandiera or best.nome)}</strong> "
                    f"({escape(best.indirizzo)}, {escape(best.comune)}): <strong>{prezzo_txt}</strong> a "
                    f"<strong>{num(best.dist_km)} km</strong>. Facendo il pieno lì risparmi "
                    f"<strong>{eur(best.risparmio, sign=True)}</strong> rispetto al prezzo medio della zona, "
                    f"considerando il costo del viaggio."
                )
                st.caption("Più un distributore è verde, più conviene")
                deck = build_fuel_deck(
                    origin, edges,
                    best_route=info.get("best_route"),
                    show_all_lines=show_all_lines,
                    raggio=raggio,
                )
                st.pydeck_chart(deck, height=480)
                st.caption(fonte)

            with style.card("top"):
                style.title("I 5 migliori")
                style.table(
                    ["Distributore", "Comune", "Prezzo", "Distanza", "Risparmio"],
                    [[escape(r.bandiera or r.nome or "Distributore"), escape(r.comune),
                      _it(f"{r.prezzo:.3f}") + " €/l", num(r.dist_km) + " km", eur(r.risparmio, sign=True)]
                     for _, r in edges.head(5).iterrows()],
                )

# --------------------------------------------------------------------------
# Archi
# --------------------------------------------------------------------------
if tab_arc.open:
    with tab_arc:
        if edges.empty:
            style.error_card("Nessun arco da mostrare: nessun distributore nel raggio scelto.")
        else:
            tab = edges.rename(
                columns={
                    "rank": "#", "bandiera": "Bandiera", "nome": "Impianto", "indirizzo": "Indirizzo", "comune": "Comune",
                    "prezzo": "Prezzo (€/l)", "dist_km": "Distanza (km)", "dev_km": "Km in più",
                    "guadagno": "Risparmio sul prezzo (€)", "brent": "Effetto Brent (€)", "costo_log": "Costo del viaggio (€)",
                    "score": "Risparmio netto (€)", "peso": "Peso arco", "peso_pos": "Peso arco (≥ 0)", "ep": "Convenienza prezzo",
                    "ep_pct": "Convenienza prezzo (posizione)", "eta_giorni": "Età prezzo (gg)",
                }
            )
            cols = ["#", "Bandiera", "Impianto", "Indirizzo", "Comune", "Prezzo (€/l)", "Distanza (km)", "Km in più",
                    "Risparmio sul prezzo (€)", "Effetto Brent (€)", "Costo del viaggio (€)", "Risparmio netto (€)", "Peso arco", "Peso arco (≥ 0)",
                    "Convenienza prezzo", "Convenienza prezzo (posizione)", "Età prezzo (gg)", "id", "lat", "lon"]
            cols = [c for c in cols if c in tab.columns]
            export = tab[cols].copy()
            export.insert(0, "origine_lat", origin[0])
            export.insert(1, "origine_lon", origin[1])

            with style.card("edges"):
                c = st.columns([1, 0.2], vertical_alignment="center")
                with c[0]:
                    style.title(f"Archi origine → distributore · {len(tab)}")
                c[1].download_button("Scarica CSV",
                                     export.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                                     file_name="archi_pesati.csv", mime="text/csv", width="stretch")
                st.dataframe(
                    tab[cols], hide_index=True, height=480, width="stretch",
                    column_config={
                        "Prezzo (€/l)": st.column_config.NumberColumn(format="%.3f"),
                        "Distanza (km)": st.column_config.NumberColumn(format="%.1f"),
                        "Km in più": st.column_config.NumberColumn(format="%.1f"),
                        "Risparmio sul prezzo (€)": st.column_config.NumberColumn(format="%+.2f"),
                        "Effetto Brent (€)": st.column_config.NumberColumn(format="%+.2f"),
                        "Costo del viaggio (€)": st.column_config.NumberColumn(format="%.2f"),
                        "Risparmio netto (€)": st.column_config.NumberColumn(format="%+.2f"),
                        "Peso arco": st.column_config.NumberColumn(format="%+.2f"),
                        "Peso arco (≥ 0)": st.column_config.NumberColumn(format="%.2f"),
                        "Convenienza prezzo": st.column_config.NumberColumn(format="%.2f"),
                        "Convenienza prezzo (posizione)": st.column_config.NumberColumn(format="%.2f"),
                        "Età prezzo (gg)": st.column_config.NumberColumn(format="%.1f"),
                    },
                )
                st.caption("Risparmio netto = risparmio sul prezzo + effetto Brent − costo del viaggio. «Peso arco» è il "
                           "risparmio netto con il segno cambiato, per cercare il cammino minimo; «Peso arco (≥ 0)» è lo "
                           "stesso spostato perché non sia mai negativo. «Convenienza prezzo» va da 1 (il più economico "
                           "della zona) a 0 (il più caro).")

# --------------------------------------------------------------------------
# Come funziona
# --------------------------------------------------------------------------
if tab_how.open:
    with tab_how, style.card("how"):
        style.title("Come funziona")
        st.markdown(
            """
L'app guarda i distributori intorno a te e stima, per ciascuno, **quanto risparmi facendo lì il rifornimento**.

- **Il prezzo**: confronta il prezzo di ogni distributore con quello tipico della zona e calcola quanto spendi
  in meno (o in più) per i litri che devi fare.
- **Il viaggio**: toglie quanto ti costa arrivarci e tornare, cioè carburante e usura dell'auto per i
  chilometri di andata e ritorno.
- **Il petrolio**: se negli ultimi giorni il Brent è salito, i prezzi alla pompa tenderanno a salire e fare
  rifornimento ora conviene un po' di più; se è sceso, conviene un po' meno. Questo vale per tutti i
  distributori allo stesso modo, quindi cambia il verdetto ma non la classifica.

Il risultato è un punteggio in euro: più è alto, più conviene. Il verdetto è **Rifornisci** se il distributore
migliore fa risparmiare (oltre la soglia scelta nelle opzioni avanzate), oppure se il serbatoio è quasi vuoto.

I prezzi e i distributori sono quelli ufficiali del MIMIT, aggiornati ogni giorno; il Brent arriva da Yahoo
Finance. Le distanze sono quelle su strada calcolate dal servizio OSRM; se non risponde, sono stimate in linea
d'aria, corrette per tenere conto delle strade.
"""
    )
    st.caption(fonte)

# --------------------------------------------------------------------------
# Colofon
# --------------------------------------------------------------------------
style.colophon()
