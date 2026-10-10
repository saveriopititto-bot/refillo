"""App Streamlit: pesi degli archi (posizione -> distributori) con lo score di rifornimento."""
from __future__ import annotations

import math
from html import escape
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit_js_eval

import fuel_model as fm
import style

st.set_page_config(page_title="Score di rifornimento", page_icon="⛽", layout="wide")
style.apply_style()

BASE = Path(__file__).parent
ANAG_FILE, PREZZI_FILE = fm.ANAG_FILE, fm.PREZZI_FILE
CACHE_ORE = 3  # i prezzi MIMIT cambiano una volta al giorno
BRENT_GIORNI = 7  # n: finestra della variazione del Brent


# --------------------------------------------------------------------------
# Formattazione
# --------------------------------------------------------------------------
def _it(s: str) -> str:
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def eur(x: float, d: int = 2, sign: bool = False) -> str:
    return _it(f"{x:{'+' if sign else ''},.{d}f}") + " €"


def num(x: float, d: int = 1) -> str:
    return _it(f"{x:,.{d}f}")


def _hex_rgb(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# --------------------------------------------------------------------------
# Dati
# --------------------------------------------------------------------------
def default_path(name: str) -> Path | None:
    for d in (BASE / "data", BASE, Path.cwd()):
        if (d / name).exists():
            return d / name
    return None


@st.cache_data(show_spinner="Leggo i CSV…")
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
    if "error" in geo:
        err = geo["error"] or {}
        return None, "Posizione non disponibile: " + GEO_ERRORI.get(err.get("code"), err.get("message", "errore sconosciuto")) + "."
    c = geo["coords"]
    lat, lon = float(c["latitude"]), float(c["longitude"])
    acc = c.get("accuracy")
    nota = f"Posizione rilevata: {lat:.5f}, {lon:.5f}" + (f" (precisione ±{acc:,.0f} m)".replace(",", ".") if acc else "")
    la0, la1, lo0, lo1 = fm.ITALY_BBOX
    if not (la0 <= lat <= la1 and lo0 <= lon <= lo1):
        nota += ". Sei fuori dall'Italia: i dati MIMIT coprono solo i distributori italiani."
    return (lat, lon), nota


def stop_with(msg: str) -> None:
    style.html(f'<div class="x-lead"><strong>⛽ Score di rifornimento</strong><br>{msg}</div>')
    st.stop()


# --------------------------------------------------------------------------
# Barra laterale
# --------------------------------------------------------------------------
sb = st.sidebar
# I contenitori fissano l'ordine visivo: i CSV caricati a mano (in Opzioni avanzate) servono prima di tutto il resto.
sb_main, sb_adv, sb_foot = (sb.container() for _ in range(3))
adv = sb_adv.expander("Opzioni avanzate")
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
                  f"({brent['data_tn']:%d/%m} → {brent['data_t']:%d/%m}, Yahoo Finance) · ΔB {db_txt}")
else:
    dB = 0.0
    nota_brent = f"Brent non disponibile da Yahoo Finance ({escape(brent_err)}): ΔB = 0"

with adv_data:
    st.caption(f"Prezzi MIMIT e Brent si scaricano da soli e si aggiornano ogni {CACHE_ORE} ore. "
               "I CSV caricati qui hanno la precedenza.")
    if st.button("Riscarica ora", width="stretch", help="Scarica di nuovo prezzi MIMIT e Brent."):
        download.clear()
        brent_yahoo.clear()
        st.rerun()

if anag_b is None or prezzi_b is None:
    errori = "<br>".join(escape(e) for e in st.session_state.get("download_err", []))
    stop_with("Non sono riuscito a scaricare i dati dal sito del MIMIT"
              + (f":<br><code>{errori}</code><br>" if errori else ". ")
              + f"Riprova più tardi, oppure carica i due CSV (<code>{ANAG_FILE}</code> e <code>{PREZZI_FILE}</code>) "
                "da «Opzioni avanzate» nella barra laterale, o mettili nella cartella <code>data/</code> accanto ad "
                "<code>app.py</code>.")

anag, prezzi, extraction = load_data(anag_b, prezzi_b)
if anag.empty or prezzi.empty:
    style.error_card("Uno dei CSV non contiene righe valide: controlla di aver caricato i file giusti.")
    st.stop()

# righe (HTML già sicuro) sui dati usati, mostrate nel riquadro della decisione
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

with sb_main:
    style.section("1 · Dove sei")
    modo_pos = st.radio("Imposta da", ["La mia posizione", "Comune", "Coordinate"], horizontal=True,
                        label_visibility="collapsed")
    origin, attesa_pos = None, ""
    if modo_pos == "La mia posizione":
        origin, nota = posizione_browser()
        attesa_pos = nota if origin is None else ""
        st.caption(nota)
        if st.button("Aggiorna posizione", width="stretch"):
            st.session_state["geo_giro"] = st.session_state.get("geo_giro", 0) + 1
            st.rerun()
    elif modo_pos == "Comune":
        comuni = sorted(anag.comune.unique())
        idx = comuni.index("GUALDO TADINO") if "GUALDO TADINO" in comuni else 0
        comune = st.selectbox("Comune", comuni, index=idx)
        sel = anag[anag.comune == comune]
        origin = (float(sel.lat.median()), float(sel.lon.median()))
        st.caption(f"Centro stimato dai distributori del comune: {origin[0]:.5f}, {origin[1]:.5f}")
    else:
        c1, c2 = st.columns(2)
        origin = (c1.number_input("Lat", value=43.2300, format="%.5f"),
                  c2.number_input("Lon", value=12.7800, format="%.5f"))

    dest = None
    if st.checkbox("Ho una destinazione", help="La deviazione diventa il detour sul percorso."):
        c1, c2 = st.columns(2)
        dest = (c1.number_input("Lat dest.", value=43.1100, format="%.5f"),
                c2.number_input("Lon dest.", value=12.3900, format="%.5f"))

    style.section("2 · Carburante")
    fuel = st.selectbox("Prodotto", fm.FUELS)
    self_service = st.radio("Modalità", ["Self", "Servito"], horizontal=True, label_visibility="collapsed") == "Self"

    style.section("3 · Veicolo")
    v_tot = st.number_input("Capacità serbatoio V_tot (l)", min_value=5.0, max_value=200.0, value=50.0, step=1.0)
    livello = st.slider("Livello attuale L", 0.0, 1.0, 0.25, 0.01, format="%.2f")
    consumo = st.number_input("Consumo (l/100 km)", min_value=1.0, max_value=40.0, value=6.5, step=0.1)
    raggio = st.slider("Raggio d'azione (km su strada)", 2, 60, 15)

with adv_model:
    livello_min = st.slider("Soglia di sicurezza L_min", 0.0, 0.5, 0.10, 0.01, format="%.2f")
    litri = None
    if st.checkbox("Imposta i litri q a mano (altrimenti pieno)"):
        litri = st.number_input("Litri q", min_value=1.0, max_value=float(v_tot),
                                value=min(30.0, float(v_tot)), step=1.0)
    usura = st.number_input("Usura variabile (€/km)", min_value=0.0, max_value=1.0, value=0.05, step=0.01,
                            format="%.3f")
    max_age = st.number_input("Età massima del prezzo (giorni)", min_value=1, max_value=60, value=7)
    road_factor = st.slider("Fattore strada / linea d'aria", 1.0, 2.0, 1.3, 0.05)
    ref_mode = st.radio("P_market = … dei prezzi nel raggio", ["mediana", "media"], horizontal=True)
    theta = st.number_input("Soglia θ (€)", value=0.0, step=0.5)
    alpha = st.slider("α (pass-through Brent)", 0.0, 0.4, 0.20, 0.01,
                      help="Quota della variazione del Brent che si trasferisce sui prezzi alla pompa.")

with sb_foot:
    style.html('<p class="x-note">Prezzi dagli open data MIMIT. Le distanze sono stimate in linea d\'aria × '
               'fattore strada.</p>')

# --------------------------------------------------------------------------
# Calcolo
# --------------------------------------------------------------------------
if origin is None:
    stop_with(escape(attesa_pos) + "<br>In alternativa scegli <strong>Comune</strong> o <strong>Coordinate</strong> "
              "in «1 · Dove sei» nella barra laterale.")
params = fm.ModelParams(
    v_tot=v_tot, livello=livello, litri=litri, alpha=alpha, delta_brent=dB,
    consumo_l100=consumo, usura_eur_km=usura, road_factor=road_factor, raggio_km=float(raggio),
    ref_mode=ref_mode, theta=theta, livello_min=livello_min,
)
cands = fm.build_candidates(anag, prezzi, fuel, self_service, float(max_age), extraction)
edges, info = fm.compute_edges(cands, origin, params, dest)

data_estrazione = f"{extraction:%d/%m/%Y}" if extraction is not None else "data sconosciuta"
fonte = (f"Estrazione MIMIT del {data_estrazione} · {len(cands):,} distributori con prezzo "
         f"{fuel} {'self' if self_service else 'servito'} valido in tutta Italia").replace(",", ".")

tab_res, tab_arc, tab_how = st.tabs(["Risultato", "Archi", "Come funziona"])

# --------------------------------------------------------------------------
# Risultato
# --------------------------------------------------------------------------
with tab_res:
    if edges.empty:
        style.error_card("Nessun distributore nel raggio scelto con un prezzo valido. "
                         "Aumenta il raggio o l'età massima del prezzo.")
        style.html(f'<p class="x-note">{"<br>".join(note_dati)}</p>')
    else:
        best = info["best"]
        prezzo_txt = _it(f"{best.prezzo:.3f}") + " €/l"
        style.lead(
            f"Il distributore migliore è <strong>{escape(best.bandiera)} · {escape(best.nome)}</strong> "
            f"({escape(best.indirizzo)}, {escape(best.comune)}): <strong>{prezzo_txt}</strong> a "
            f"<strong>{num(best.dist_km)} km</strong>. Facendo {num(info['q'])} litri lì risparmi "
            f"<strong>{eur(best.score, sign=True)}</strong> rispetto al prezzo tipico della zona, "
            f"già tolto il costo della deviazione."
        )
        corpo = escape(_it(info["motivo"][0].upper() + info["motivo"][1:])) + "."
        if not info["decisione"]:
            corpo += " Il termine Brent è uguale per tutti i distributori: sposta lo score ma non cambia la classifica."
        style.hero("Decisione", "Rifornisci" if info["decisione"] else "Non conviene",
                   f"S migliore {eur(best.score, sign=True)}", corpo, ok=info["decisione"], meta_html=note_dati)
        style.metrics([
            ("Prezzo di mercato", _it(f"{info['p_market']:.3f}") + " €/l",
             f"{ref_mode} dei {info['n']} distributori nel raggio"),
            ("Distributori nel raggio", str(info["n"]), f"entro {raggio} km su strada"),
            ("Litri q", num(info["q"]) + " l", "pieno" if litri is None else "impostati a mano"),
            ("Costo al km", _it(f"{info['c_km']:.3f}") + " €/km", "carburante + usura"),
        ])

        with style.card("map"):
            style.title("Dove conviene andare")
            st.caption("Punto blu scuro = la tua posizione. Più un distributore è verde-azzurro, più conviene; "
                       "arancione = conviene poco.")
            smin, smax = edges.score.min(), edges.score.max()
            lo_rgb, hi_rgb = _hex_rgb(style.ORANGE), _hex_rgb(style.BLUE_GREEN)

            def colore(s: float) -> list[int]:
                t = 1.0 if smax == smin else (s - smin) / (smax - smin)
                return [int(a + (b - a) * t) for a, b in zip(lo_rgb, hi_rgb)] + [220]

            mappa = edges.copy()
            mappa["colore"] = mappa.score.map(colore)
            mappa["etichetta"] = (
                mappa.bandiera + " · " + mappa.nome + "\n" + mappa.prezzo.map(lambda x: _it(f"{x:.3f}") + " €/l")
                + " · S = " + mappa.score.map(lambda x: eur(x, sign=True))
                + " · " + mappa.dist_km.map(lambda x: num(x) + " km")
            )
            mappa["src"] = [[origin[1], origin[0]]] * len(mappa)
            mappa["tgt"] = mappa[["lon", "lat"]].values.tolist()
            layers = [
                pdk.Layer("LineLayer", data=mappa, get_source_position="src", get_target_position="tgt",
                          get_color="colore", get_width=2, width_min_pixels=1),
                pdk.Layer("ScatterplotLayer", data=mappa, get_position=["lon", "lat"], get_fill_color="colore",
                          get_radius=120, radius_min_pixels=5, radius_max_pixels=14, pickable=True),
                pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{"lat": origin[0], "lon": origin[1]}]),
                          get_position=["lon", "lat"], get_fill_color=list(_hex_rgb(style.DEEP)) + [255],
                          get_radius=150, radius_min_pixels=8, radius_max_pixels=16),
            ]
            zoom = max(5.0, 12.2 - math.log2(max(raggio, 2) / 5))
            st.pydeck_chart(
                pdk.Deck(layers=layers, map_style="light",
                         initial_view_state=pdk.ViewState(latitude=origin[0], longitude=origin[1], zoom=zoom),
                         tooltip={"text": "{etichetta}"}),
                height=480,
            )
            st.caption(fonte)

        with style.card("top"):
            style.title("I 5 migliori")
            style.table(
                ["#", "Distributore", "Comune", "Prezzo", "Distanza", "S"],
                [[str(r["rank"]), escape(f"{r.bandiera} · {r.nome}"), escape(r.comune),
                  _it(f"{r.prezzo:.3f}") + " €/l", num(r.dist_km) + " km", eur(r.score, sign=True)]
                 for _, r in edges.head(5).iterrows()],
            )

# --------------------------------------------------------------------------
# Archi
# --------------------------------------------------------------------------
with tab_arc:
    if edges.empty:
        style.error_card("Nessun arco da mostrare: nessun distributore nel raggio scelto.")
    else:
        tab = edges.rename(
            columns={
                "rank": "#", "bandiera": "Bandiera", "nome": "Impianto", "indirizzo": "Indirizzo", "comune": "Comune",
                "prezzo": "P_i (€/l)", "dist_km": "Distanza (km)", "dev_km": "D_i (km)",
                "guadagno": "Guadagno (€)", "brent": "Brent (€)", "costo_log": "Costo logistico (€)",
                "score": "S_i (€)", "peso": "Peso w = −S", "peso_pos": "Peso w ≥ 0", "ep": "E_p",
                "ep_pct": "E_p (percentile)", "eta_giorni": "Età prezzo (gg)",
            }
        )
        cols = ["#", "Bandiera", "Impianto", "Indirizzo", "Comune", "P_i (€/l)", "Distanza (km)", "D_i (km)",
                "Guadagno (€)", "Brent (€)", "Costo logistico (€)", "S_i (€)", "Peso w = −S", "Peso w ≥ 0",
                "E_p", "E_p (percentile)", "Età prezzo (gg)", "id", "lat", "lon"]
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
                    "P_i (€/l)": st.column_config.NumberColumn(format="%.3f"),
                    "Distanza (km)": st.column_config.NumberColumn(format="%.1f"),
                    "D_i (km)": st.column_config.NumberColumn(format="%.1f"),
                    "Guadagno (€)": st.column_config.NumberColumn(format="%+.2f"),
                    "Brent (€)": st.column_config.NumberColumn(format="%+.2f"),
                    "Costo logistico (€)": st.column_config.NumberColumn(format="%.2f"),
                    "S_i (€)": st.column_config.NumberColumn(format="%+.2f"),
                    "Peso w = −S": st.column_config.NumberColumn(format="%+.2f"),
                    "Peso w ≥ 0": st.column_config.NumberColumn(format="%.2f"),
                    "E_p": st.column_config.NumberColumn(format="%.2f"),
                    "E_p (percentile)": st.column_config.NumberColumn(format="%.2f"),
                    "Età prezzo (gg)": st.column_config.NumberColumn(format="%.1f"),
                },
            )
            st.caption("Peso w = −S per il cammino minimo; w ≥ 0 = S_max − S se servono pesi non negativi.")

# --------------------------------------------------------------------------
# Come funziona
# --------------------------------------------------------------------------
with tab_how, style.card("how"):
    style.title("Come funziona")
    st.markdown(
        """
L'app guarda i distributori intorno a te e stima, per ciascuno, **quanto risparmi facendo lì il rifornimento**.

- **Il prezzo**: confronta il prezzo di ogni distributore con quello tipico della zona e calcola quanto spendi
  in meno (o in più) per i litri che devi fare.
- **Il viaggio**: toglie quanto ti costa arrivarci, cioè carburante e usura dell'auto per i chilometri in più.
  Se indichi una destinazione conta solo la deviazione dal percorso, altrimenti andata e ritorno.
- **Il petrolio**: se negli ultimi giorni il Brent è salito, i prezzi alla pompa tenderanno a salire e fare
  rifornimento ora conviene un po' di più; se è sceso, conviene un po' meno. Questo vale per tutti i
  distributori allo stesso modo, quindi cambia il verdetto ma non la classifica.

Il risultato è un punteggio in euro: più è alto, più conviene. Il verdetto è **Rifornisci** se il distributore
migliore fa risparmiare (oltre la soglia scelta nelle opzioni avanzate), oppure se il serbatoio è quasi vuoto.

I prezzi e i distributori sono quelli ufficiali del MIMIT, aggiornati ogni giorno; il Brent arriva da Yahoo
Finance. Le distanze sono stimate in linea d'aria, corrette per tenere conto delle strade.
"""
    )
    with st.expander("La formula, per chi vuole i dettagli"):
        st.markdown(
            r"""
$$S_i = q\,\big[(P_{market}-P_i)+\alpha\,P_{market}\,\Delta B\big]-D_i\,C_{km}$$

- **q**: litri acquistati (`V_tot·(1−L)` se pieno).
- **P_market**: mediana/media dei prezzi dei distributori nel raggio.
- **ΔB**: variazione relativa del Brent in euro negli ultimi 7 giorni (scaricata da Yahoo Finance), limitata a ±10%; **α** è la quota di pass-through.
- **D_i**: deviazione. Senza destinazione è andata e ritorno (2·d); con destinazione è `d(o,i)+d(i,dest)−d(o,dest)`.
- **C_km** = consumo/100 · P_market + usura.
- **Peso dell'arco**: `w = −S_i` (cammino minimo), oppure `w = S_max − S_i` se servono pesi non negativi.
- **E_p**: efficienza posizionale, `1 − (P_i−P_min)/(P_max−P_min)`; la versione percentile resiste agli outlier.
- Si rifornisce se `S_max > θ`, oppure se `L < L_min`.
"""
        )
    st.caption(fonte)
