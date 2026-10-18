"""Stile (lo stesso di test4): CSS globale e blocchi HTML usati dalle viste di ui/."""
from __future__ import annotations

from collections.abc import Sequence
from html import escape
import time

import streamlit as st

# palette
SKY = "#8ecae6"
BLUE_GREEN = "#219ebc"
DEEP = "#023047"
AMBER = "#ffb703"
ORANGE = "#fb8500"
# sfumature ricavate dalla palette
BG = "#eef6fa"
N100, N200, N300, N500, N700 = "#f2f8fb", "#e2eef4", "#c9dde7", "#7c9fb2", "#3a5f74"
A100, A600, A700 = "#fff3e6", "#e07600", "#a65600"
# colori dell'indicatore del petrolio (rosso solo per «Aspetta», verde per gli altri)
VERDE, ROSSO = "#1f9d55", "#d64545"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;800&display=swap');
:root {{ --radius-lg: 22px; --radius-md: 14px;
  --shadow-soft: 0 1px 2px rgba(2,48,71,.04), 0 10px 30px rgba(2,48,71,.07); }}
html, body, .stApp {{ font-family: 'Archivo', system-ui, sans-serif; }}
.stApp {{ background: {BG}; color: {DEEP}; }}
/* aggiornamenti senza grigio: Streamlit sbiadisce gli elementi mentre ricalcola; qui restano nitidi e cambia solo il
   contenuto (per le attese lunghe c'è il cerchio di caricamento). Niente omino «Running» in alto. */
[data-stale="true"] {{ opacity: 1 !important; transition: none !important; }}
[data-testid="stStatusWidget"] {{ visibility: hidden; }}
.stApp *:not(svg *) {{ transition: background-color .2s ease, color .2s ease, box-shadow .2s ease, border-color .2s ease; }}
h1, h2, h3, h4, h5, h6 {{ font-weight: 800 !important; letter-spacing: -0.015em; color: {DEEP}; }}
[data-testid="stHeaderActionElements"] {{ display: none; }}
hr {{ display: none; }}

/* pagina */
header[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stMainBlockContainer"] {{ padding: 8px 12px 8px; max-width: 1040px; margin: 0 auto; }}
[data-testid="stMain"] [data-testid="stVerticalBlock"] {{ gap: 6px; }}

/* barra laterale disattivata: tutti i controlli sono integrati nella pagina centrale */
section[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
button[data-testid="stSidebarCollapseButton"] {{ display: none !important; }}

/* scheda controlli sotto il riquadro del consiglio */
[class*="st-key-card-controls"] {{ padding: 20px 24px; gap: 14px !important; }}
[class*="st-key-card-controls"] [data-testid="stHorizontalBlock"] {{ gap: 20px; }}
[class*="st-key-card-controls"] [data-testid="stExpander"] {{ margin-top: 4px; }}
[class*="st-key-card-controls"] [data-testid="stExpander"] summary {{ padding: 8px 14px; font-weight: 600; font-size: 14px; }}
[class*="st-key-card-controls"] [data-testid="stExpanderDetails"] {{ padding: 12px 14px 16px; }}
.stRadio [role="radiogroup"] {{ gap: 0 16px; }}
.stRadio [data-testid="stWidgetLabel"] p {{ font-size: 12px; font-weight: 800;
  letter-spacing: .08em; text-transform: uppercase; color: {N700}; }}
.stRadio label p {{ font-size: 13px; color: {DEEP}; }}
[data-testid="stRadioOption"]:not([data-selected="true"]) > div > div:first-child {{
  background: #fff; border: 1.5px solid {N500}; }}
[data-testid="stRadioOption"]:not([data-selected="true"]):hover > div > div:first-child {{ border-color: {ORANGE}; }}

/* campi */
[data-baseweb="input"], [data-baseweb="base-input"], [data-testid="stNumberInputContainer"] {{
  background: {N100} !important; border: 1px solid transparent !important; border-radius: var(--radius-md) !important; }}
[data-baseweb="input"]:hover, [data-testid="stNumberInputContainer"]:hover {{ border-color: {N300} !important; }}
[data-baseweb="input"]:focus-within, [data-testid="stNumberInputContainer"]:focus-within {{
  border-color: {BLUE_GREEN} !important; background: #fff !important; }}
[data-baseweb="input"] input {{ background: transparent; color: {DEEP}; }}
[data-testid="stNumberInputStepDown"], [data-testid="stNumberInputStepUp"] {{ background: transparent; border-radius: 10px; }}
[data-testid="stSlider"] [role="slider"] {{ box-shadow: 0 2px 6px rgba(2,48,71,.2); }}
[data-testid="stSliderThumbValue"] {{ color: {DEEP}; font-weight: 800; }}
[data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child {{ border-radius: 999px; }}
[data-testid="stTooltipIcon"] svg {{ stroke: {N500}; }}

/* un solo riquadro bianco con le pillole e tutto il contenuto delle schede: le schede interne perdono sfondo e
   ombra, gli indicatori diventano riquadri tenui */
.st-key-card-schede [class*="st-key-card"] {{ background: transparent; box-shadow: none; padding: 0;
  border-radius: 0; }}
.st-key-card-schede [class*="st-key-card"] + [class*="st-key-card"],
.st-key-card-schede [data-testid="stElementContainer"] + [class*="st-key-card"] {{ margin-top: 0; }}
.st-key-card-schede .x-metric {{ background: {N100}; box-shadow: none; }}

/* schede */
[class*="st-key-card"] {{ position: relative; background: #fff; border: 1px solid transparent; border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft); padding: 14px; gap: 6px !important; }}
.x-title {{ margin: 0; font-size: 20px; line-height: 1.25; font-weight: 800; letter-spacing: -0.015em; color: {DEEP}; }}
[class*="st-key-card"] p {{ font-size: 14px; }}
.st-key-card-how p, .st-key-card-how li {{ font-size: 15px; line-height: 1.6; }}
[class*="st-key-card"] [data-testid="stCaptionContainer"] p {{ font-size: 12px; line-height: 1.35; color: {N700}; }}
[class*="st-key-card"] [data-testid="stDataFrame"] {{ border-radius: var(--radius-md); overflow: hidden; }}
/* mappa Leaflet (cornice di st.iframe): quadrata, a qualunque larghezza dello schermo; al massimo 360 px di
   larghezza (360 × 360), centrata; da telefono il 90% della larghezza */
.st-key-mappa iframe {{ display: block; height: auto !important; aspect-ratio: 1 / 1; width: 100% !important;
  max-width: 360px; margin: 0 auto; border: 0; border-radius: var(--radius-md); }}
@media (max-width: 640px) {{ .st-key-mappa iframe {{ width: 90% !important; }} }}
/* Streamlit fissa il contenitore a 400 px (flex: 0 0 400px): senza questa regola, da telefono restano ~80 px vuoti
   sotto la mappa */
.st-key-mappa [data-testid="stElementContainer"] {{ height: auto !important; flex: 0 0 auto !important; }}

/* bottoni: compatti a pillola allineati alla barra dei risultati */
.stButton button, .stDownloadButton button {{ border-radius: 999px; border: 0; padding: 8px 14px;
  font-weight: 700; min-height: 36px; line-height: 1.2; }}
.stButton button p, .stDownloadButton button p {{ font-weight: 700; font-size: 13.5px; margin: 0; }}
.stButton button[kind="primary"] {{ background: {ORANGE}; color: {DEEP}; }}
.stButton button[kind="primary"]:hover {{ background: {A600}; color: {DEEP}; }}
.stButton button[kind="secondary"], .stDownloadButton button {{ background: {N200}; color: {DEEP}; }}
.stButton button[kind="secondary"]:hover, .stDownloadButton button:hover {{ background: {N300}; color: {DEEP}; }}

/* opzioni avanzate: riquadro tenue a pillola compatto allineato ai controlli */
[data-testid="stExpander"] details {{ border: 0; background: {N100}; border-radius: 999px; transition: border-radius .15s ease-out; }}
[data-testid="stExpander"] details[open] {{ border-radius: var(--radius-md); }}
[data-testid="stExpander"] summary {{ min-height: 36px; padding: 7px 14px; font-weight: 700; font-size: 13.5px;
  color: {DEEP}; cursor: pointer; }}
[data-testid="stExpander"] summary:hover {{ color: {ORANGE}; }}

/* riga dei comandi (Home, Posizione, Opzioni, Top 5, F.A.Q.): sempre orizzontale, cinque pillole della stessa
   larghezza che riempiono tutta la riga, a qualunque larghezza dello schermo. Opzioni e Top 5 sono popover:
   si aprono sopra la pagina, la riga non va mai a capo */
.st-key-comandi [data-testid="stHorizontalBlock"] {{
  display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
  gap: 8px !important; align-items: stretch !important;
}}
.st-key-comandi [data-testid="stColumn"] {{
  flex: 1 1 0 !important; min-width: 0 !important; width: auto !important;
}}
/* tutte le pillole con lo sfondo tenue e il testo normale (niente grassetto); tra Home e F.A.Q. quella aperta
   (type="primary") è in blu scuro */
.st-key-comandi button {{ width: 100% !important; min-height: 36px !important; padding: 6px 8px !important;
  border: 0 !important; border-radius: 999px !important; background: {N100} !important; color: {DEEP} !important;
  justify-content: center !important; gap: 2px !important; }}
.st-key-comandi button p {{ font-weight: 400 !important; font-size: 13px !important; color: {DEEP}; margin: 0;
  white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }}
.st-key-comandi button:hover p {{ color: {ORANGE}; }}
.st-key-comandi button[kind="primary"] {{ background: {DEEP} !important; }}
.st-key-comandi button[kind="primary"] p, .st-key-comandi button[kind="primary"]:hover p {{ color: #fff; }}
/* freccia del popover attaccata al testo */
.st-key-comandi button > div {{ gap: 2px !important; justify-content: center !important; }}
.st-key-comandi button [data-testid="stIconMaterial"] {{ margin: 0 !important; font-size: 16px !important; }}
/* menu del carburante (Home, accanto a «Costo al km»): pillola alta 28 px (30 da telefono), testo centrato */
.st-key-carb [data-baseweb="select"] > div {{
  min-height: 28px !important; border-radius: 999px !important; padding: 0 6px !important;
}}
.st-key-carb [data-testid="stSelectbox"] > div > div {{ height: 28px !important; min-height: 0 !important;
  border-radius: 999px !important; display: flex !important; align-items: center !important; overflow: hidden; }}
.st-key-carb [data-testid="stSelectbox"] input,
.st-key-carb [data-testid="stSelectbox"] button {{ height: 100% !important; min-height: 0 !important;
  padding-top: 0 !important; padding-bottom: 0 !important; }}
/* voci dell'elenco aperto della stessa misura del menu */
[role="listbox"] [role="option"] {{ font-size: 13px !important; min-height: 32px !important;
  padding-top: 4px !important; padding-bottom: 4px !important; }}
.st-key-carb [data-baseweb="select"] *,
.st-key-carb [data-testid="stSelectbox"] input {{
  font-size: 12.5px !important; font-weight: 700 !important; white-space: nowrap !important;
}}

/* blocchi HTML: Streamlit dà margin-bottom -16px al contenitore markdown */
[data-testid="stMarkdownContainer"]:has(> [class^="x-"]) {{ margin-bottom: 0; }}
.x-sec {{ font-size: 11px; letter-spacing: .1em; text-transform: uppercase; font-weight: 800; color: {N700};
  margin-top: 4px; }}
.x-lead {{ font-size: 15px; line-height: 1.45; text-align: justify; text-justify: inter-word; color: {DEEP}; }}
.x-lead strong {{ color: {A700}; }}
.x-label {{ font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: {N700}; }}
/* indicatori: riquadri compatti, sempre tutti su una riga */
.x-metrics {{ display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); gap: 10px; }}
.x-metric {{ background: #fff; border-radius: var(--radius-md); box-shadow: var(--shadow-soft); padding: 10px 14px;
  display: flex; flex-direction: column; gap: 2px; min-width: 0; }}
.x-metric .x-label {{ font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.x-metric .v {{ font-size: 20px; font-weight: 800; letter-spacing: -.02em; line-height: 1.15; font-variant-numeric: tabular-nums;
  white-space: nowrap; }}
/* riga degli indicatori della Home: tre indicatori e il menu del carburante, quattro riquadri larghi uguali */
.st-key-metriche [data-testid="stHorizontalBlock"] {{ gap: 10px !important; flex-wrap: nowrap !important;
  align-items: stretch !important; }}
.st-key-metriche [data-testid="stColumn"] {{ min-width: 0 !important; width: auto !important; }}
.st-key-metriche [data-testid="stColumn"]:first-child {{ flex: 1 1 0 !important; }}
.st-key-metriche [data-testid="stColumn"]:last-child {{ flex: 0 0 calc((100% - 30px) / 4) !important; }}
/* tutti alti come la riga: il menu e gli indicatori (che da telefono largo stanno su una riga sola) si allineano */
.st-key-metriche [data-testid="stColumn"] div:has(.st-key-carb),
.st-key-metriche [data-testid="stColumn"] div:has(.x-metrics),
.st-key-metriche .x-metrics {{ height: 100%; }}
/* da computer «Benzina» sta sulla riga dei valori degli indicatori: scritta in alto e menu subito sotto */
.st-key-carb {{ background: {N100}; border-radius: var(--radius-md); padding: 12px 14px 10px; gap: 1px !important;
  height: 100%; justify-content: flex-start; min-width: 0; }}
.st-key-carb .x-label {{ font-size: 10px; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.x-metric .s {{ font-size: 12px; line-height: 1.3; color: {N700}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
@media (max-width: 640px) {{
  [class*="st-key-card-controls"] {{ padding: 14px 10px !important; }}
  /* da telefono margini minimi: pagina quasi a tutta larghezza e riquadri con poco bordo interno */
  [data-testid="stMainBlockContainer"] {{ padding: 4px 6px 4px !important; }}
  [class*="st-key-card"] {{ padding: 10px; }}
  .st-key-comandi [data-testid="stHorizontalBlock"] {{ gap: 4px !important; }}
  .st-key-comandi button {{ min-height: 32px !important; padding: 4px 2px !important; }}
  .st-key-comandi button p {{ font-size: 11.5px !important; }}
  /* niente freccia dei popover da telefono: c'è poco spazio */
  .st-key-comandi button div[aria-hidden="true"]:has([data-testid="stIconMaterial"]) {{ display: none !important; }}
  .st-key-carb [data-baseweb="select"] > div {{ min-height: 32px !important; padding: 0 4px !important; }}
  .st-key-carb [data-baseweb="select"] *,
  .st-key-carb [data-testid="stSelectbox"] input {{ font-size: 11px !important; }}
  .stButton button, .stDownloadButton button {{ padding: 6px 10px; min-height: 32px; }}
  .stButton button p, .stDownloadButton button p {{ font-size: 12px; font-weight: 700; }}
  [data-testid="stExpander"] summary {{ min-height: 32px; padding: 5px 10px; font-size: 12px; }}
  .st-key-card-schede {{ padding: 8px !important; }}
  .x-metrics {{ gap: 6px; }}
  /* da telefono i valori salgono all'altezza di «Benzina»: scritta su una riga sola e 6 px sotto il valore */
  .x-metric {{ padding: 8px 6px; justify-content: space-between; }}
  .x-metric .x-label {{ font-size: 9px; letter-spacing: .01em; white-space: nowrap; line-height: 1.25; }}
  .x-metric .v {{ font-size: 13px; letter-spacing: -.03em; margin-bottom: 6px; }}
  .x-metric .s {{ display: none; }}
  .st-key-metriche [data-testid="stHorizontalBlock"] {{ gap: 6px !important; }}
  .st-key-metriche [data-testid="stColumn"]:last-child {{ flex-basis: calc((100% - 18px) / 4) !important; }}
  .st-key-carb {{ padding: 8px 6px 6px; gap: 0 !important; }}
  .st-key-carb .x-label {{ font-size: 9px; letter-spacing: .03em; }}
  /* da telefono niente freccia nel menu: il nome del carburante resta intero */
  .st-key-carb [data-testid="stSelectbox"] button {{ display: none !important; }}
  .st-key-carb [data-testid="stSelectbox"] input {{ text-align: center; padding-left: 4px !important;
    padding-right: 4px !important; }}
}}
.x-hero {{ background: linear-gradient(135deg, {DEEP}, #04466a); color: #fff; border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft); padding: 16px 22px; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 8px 28px; align-items: center; }}
.x-hero .k {{ font-size: 10px; letter-spacing: .1em; text-transform: uppercase; font-weight: 600; color: {SKY}; }}
.x-hero .v {{ font-size: 26px; font-weight: 800; letter-spacing: -.03em; line-height: 1; color: {AMBER}; }}
.x-hero .m {{ font-size: 12px; line-height: 1.4; color: {SKY}; margin: 2px 0; }}
.x-hero p {{ margin: 0; font-size: 14px; line-height: 1.35; text-wrap: pretty; color: #fff; }}
.x-hero p.x-hero-nota {{ margin-top: 2px; color: {N200}; max-width: 62ch; }}
.x-cerchio {{ display: inline-flex; line-height: 0; filter: drop-shadow(0 2px 6px rgba(2,48,71,.25)); }}
.x-hero-aside {{ display: flex; align-items: center; justify-content: flex-end; margin: -8px 0; }}
.x-hero-aside svg {{ width: 90px; height: 90px; }}
@media (max-width: 640px) {{ .x-hero-aside svg {{ width: 68px; height: 68px; }} }}
/* riquadro «Consiglio» con il testo a sinistra e, a destra, il cerchio dello score:
   le due colonne restano affiancate anche da telefono */
.st-key-hero {{ background: linear-gradient(135deg, {DEEP}, #04466a); color: #fff; border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft); padding: 12px 14px 12px 16px; }}
.st-key-hero [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 16px !important; }}
.st-key-hero [data-testid="stColumn"]:first-child {{ flex: 1 1 0 !important; min-width: 0 !important; width: auto !important; }}
.st-key-hero [data-testid="stColumn"]:last-child {{ flex: 0 0 92px !important; min-width: 0 !important; width: auto !important; }}
.st-key-hero .x-hero {{ background: none; box-shadow: none; padding: 0; border-radius: 0; display: flex;
  flex-direction: column; align-items: stretch; gap: 4px; }}
.st-key-hero .x-hero-aside {{ justify-content: center; margin: 0 0 4px; }}
.stApp .st-key-hero .x-note {{ color: {SKY}; font-size: 11px; line-height: 1.3; margin-top: 4px; }}
/* «📍 Perugia (stima)» sulla riga di «CONSIGLIO»: nessuna altezza in più */
.x-hero .k .x-pos {{ text-transform: none; letter-spacing: 0; font-weight: 400; cursor: help; white-space: nowrap; }}
@media (max-width: 640px) {{
  .st-key-hero {{ padding: 6px 10px 6px 12px; }}
  .x-hero .v {{ font-size: 23px; }}
  .x-hero p {{ font-size: 13px; line-height: 1.25; }}
  .st-key-hero .x-hero {{ gap: 2px; }}
  .x-lead {{ font-size: 14px; line-height: 1.4; }}
  [class*="st-key-card"] [data-testid="stCaptionContainer"] p {{ font-size: 10.5px; line-height: 1.25; }}
  .st-key-hero [data-testid="stHorizontalBlock"] {{ gap: 10px !important; }}
  .st-key-carb [data-testid="stSelectbox"] > div > div {{ height: 30px !important; }}
  .st-key-hero [data-testid="stColumn"]:last-child {{ flex-basis: 68px !important; }}
}}
.x-err {{ background: {A100}; color: {A700}; font-weight: 600; border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft); padding: 20px 24px; }}
.x-scroll {{ overflow-x: auto; }}
.x-table, .x-table tr {{ border: 0; }}
.x-table {{ width: 100%; margin: 0; border-collapse: collapse; font-size: 14px; font-variant-numeric: tabular-nums; }}
.x-table th {{ text-align: left; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: {N700};
  padding: 8px; border: 0; font-weight: 400; background: transparent; }}
.x-table td {{ padding: 8px; border: 0; white-space: nowrap; }}
.x-table tbody tr:nth-child(odd) td {{ background: {N100}; }}
.x-table tbody tr td:first-child {{ border-radius: 10px 0 0 10px; font-weight: 600; }}
.x-table tbody tr td:last-child {{ border-radius: 0 10px 10px 0; }}
/* «Top 5» (popover, fuori dalla riga dei comandi) da telefono: senza la colonna Comune (nel raggio è quasi sempre
   la stessa) e con il testo più piccolo, così distanza e risparmio restano visibili */
@media (max-width: 640px) {{
  [data-testid="stPopoverBody"] .x-table {{ font-size: 12px; }}
  [data-testid="stPopoverBody"] .x-table th, [data-testid="stPopoverBody"] .x-table td {{ padding: 6px 5px; }}
  [data-testid="stPopoverBody"] .x-table th {{ font-size: 9.5px; letter-spacing: .02em; }}
  [data-testid="stPopoverBody"] .x-table th:nth-child(2),
  [data-testid="stPopoverBody"] .x-table td:nth-child(2) {{ display: none; }}
}}
.stApp .x-note {{ font-size: 12px; line-height: 1.45; color: {N700}; margin: 0; }}
[data-testid="stCaptionContainer"] p {{ font-size: 12px; line-height: 1.45; color: {N700}; }}
/* componente invisibile che chiede la posizione al browser: niente spazio vuoto */
[data-testid="stElementContainer"]:has(iframe[title^="streamlit_js_eval"]) {{ position: absolute; width: 0; height: 0;
  overflow: hidden; margin: 0; }}

/* cerchio di caricamento: uno solo, al centro dello schermo, su sfondo pieno che copre la pagina (MIMIT, Brent, score,
   posizione).
   Con .x-ritardo compare dopo un attimo, così non lampeggia quando i dati sono già in memoria. */
.x-progress-wrap {{ position: fixed; inset: 0; z-index: 999990; display: flex; justify-content: center;
  align-items: center; padding: 16px; background: {BG}; }}
.x-progress-wrap.x-ritardo {{ opacity: 0; animation: x-compari .15s ease-out .3s forwards; }}
@keyframes x-compari {{ to {{ opacity: 1; }} }}
.x-progress-box {{ background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-soft);
  padding: 26px 32px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 14px; max-width: 320px; width: 100%; text-align: center; }}
.x-progress-lbl {{ font-size: 13px; font-weight: 700; color: {DEEP}; line-height: 1.35; letter-spacing: -0.01em; }}
[data-testid="stElementContainer"]:has(.x-progress-wrap) {{ position: absolute; width: 0; height: 0; margin: 0; }}
/* schermata d'avvio: lo stesso riquadro del cerchio di caricamento, con il pulsante (icona Material del distributore,
   verde come il cerchio) al posto del cerchio */
.stApp .st-key-avvio {{ position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 999990;
  background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-soft); padding: 31px 38px;
  width: min(384px, calc(100vw - 32px)); align-items: center; gap: 17px; text-align: center; }}
.stApp .st-key-avvio .stButton button {{ width: 132px; height: 132px; min-height: 0; padding: 0; border-radius: 50%;
  background: #fff; border: 8px solid {VERDE}; color: {VERDE}; box-shadow: none; transition: background .15s, transform .15s; }}
.stApp .st-key-avvio .stButton button:hover {{ background: #e8f5ee; color: {VERDE}; transform: scale(1.04); }}
.stApp .st-key-avvio .x-progress-lbl {{ text-align: center; font-size: 15.5px; }}
/* menu del carburante: pillola su sfondo tenue, come quello della Home */
.stApp .st-key-avvio [data-testid="stElementContainer"]:has([data-testid="stSelectbox"]) {{ width: 190px !important; }}
.stApp .st-key-avvio [data-baseweb="select"] > div {{ min-height: 38px !important; border-radius: 999px !important;
  padding: 0 6px !important; background: {N100} !important; border-color: {N200} !important; }}
.stApp .st-key-avvio [data-testid="stSelectbox"] > div > div {{ height: 38px !important; min-height: 0 !important;
  border-radius: 999px !important; display: flex !important; align-items: center !important; overflow: hidden; }}
.stApp .st-key-avvio [data-testid="stSelectbox"] input,
.stApp .st-key-avvio [data-testid="stSelectbox"] button {{ height: 100% !important; min-height: 0 !important;
  padding-top: 0 !important; padding-bottom: 0 !important; }}
.stApp .st-key-avvio [data-baseweb="select"] *,
.stApp .st-key-avvio [data-testid="stSelectbox"] input {{ font-size: 14px !important; font-weight: 700 !important;
  color: {DEEP} !important; white-space: nowrap !important; }}
.stApp .st-key-avvio .stButton button p {{ font-size: 60px; line-height: 1; color: {VERDE}; }}
@media (max-width: 640px) {{
  .x-progress-box {{ padding: 18px 20px; max-width: 260px; gap: 10px; }}
  .x-progress-box svg {{ width: 95px; height: 95px; }}
  .x-progress-lbl {{ font-size: 12px; }}
  .stApp .st-key-avvio {{ padding: 22px 24px; width: min(312px, calc(100vw - 32px)); gap: 12px; }}
  .stApp .st-key-avvio .x-progress-lbl {{ font-size: 14.5px; }}
  .stApp .st-key-avvio .stButton button {{ width: 114px; height: 114px; border-width: 7px; }}
  .stApp .st-key-avvio .stButton button p {{ font-size: 52px; }}
}}

/* colofon */
.x-colophon {{ display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap;
  padding: 2px 8px 0; font-size: 12px; color: {N700}; text-align: center; }}
.x-colophon-brand {{ font-weight: 800; letter-spacing: -0.015em; color: {DEEP}; }}
.x-colophon-ver {{ display: inline-flex; align-items: center; font-size: 11px; font-weight: 700;
  padding: 1px 7px; border-radius: 999px; background: {N200}; color: {BLUE_GREEN}; letter-spacing: .02em; }}
.x-colophon-dot {{ color: {N500}; }}
.x-colophon-text {{ color: {N700}; font-size: 12px; }}

/* invito a installare l'app (solo da telefono, nella Home): striscia bianca fissa in fondo, sopra la pagina */
.stApp .st-key-installa {{ position: fixed; left: 12px; right: 12px; bottom: 14px; z-index: 999980; max-width: 480px;
  margin: 0 auto; background: #fff; border-radius: 16px; border-left: 5px solid {AMBER};
  box-shadow: 0 6px 24px rgba(2, 48, 71, .25); padding: 10px 30px 10px 12px; gap: 12px !important;
  align-items: center; flex-wrap: nowrap !important; width: auto !important; }}
.stApp .st-key-installa [data-testid="stElementContainer"] {{ width: auto !important; }}
.stApp .st-key-installa .x-installa {{ display: flex; align-items: center; gap: 12px; }}
.stApp .st-key-installa .x-installa-ic {{ width: 42px; height: 42px; border-radius: 12px; flex: none;
  background: #fff; border: 3px solid {VERDE}; color: {VERDE}; display: flex; align-items: center;
  justify-content: center; box-sizing: border-box; }}
.stApp .st-key-installa .x-installa-txt {{ font-size: 12.5px; line-height: 1.35; color: {N700}; }}
.stApp .st-key-installa .x-installa-txt b {{ display: block; font-size: 14px; color: {DEEP}; }}
.stApp .st-key-installa [data-testid="stLinkButton"] a {{ background: {ORANGE}; color: #fff !important;
  border: 0; border-radius: 999px; min-height: 0; padding: 7px 14px; white-space: nowrap; }}
.stApp .st-key-installa [data-testid="stLinkButton"] a p {{ font-weight: 700; font-size: 13px; }}
.stApp .st-key-installa [data-testid="stElementContainer"]:has(.stButton) {{ position: absolute; top: 2px; right: 2px; }}
.stApp .st-key-installa .stButton button {{ border: 0; background: none; min-height: 0; padding: 2px 6px;
  color: {N500}; box-shadow: none; }}
.stApp .st-key-installa .stButton button p {{ font-size: 18px; line-height: 1; }}
.stApp .st-key-installa [data-testid="stElementContainer"]:has(.x-installa) {{ flex: 1 1 auto; min-width: 0; }}
@media (min-width: 641px) {{ .stApp .st-key-installa {{ display: none; }} }}
</style>
"""


def apply_style() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def html(s: str) -> None:
    st.markdown(s, unsafe_allow_html=True)


def card(key: str):
    """Scheda bianca arrotondata (container con chiave, stilizzato via CSS)."""
    return st.container(key=f"card-{key}")


def title(text: str) -> None:
    html(f'<div class="x-title">{escape(text)}</div>')


def metrics(items: Sequence[tuple[str, str, str]]) -> None:
    cells = "".join(
        f'<div class="x-metric"><span class="x-label">{escape(lbl)}</span>'
        f'<span class="v">{escape(val)}</span><span class="s">{escape(sub)}</span></div>'
        for lbl, val, sub in items)
    html(f'<div class="x-metrics">{cells}</div>')


def section(text: str) -> None:
    """Titoletto di sezione (in «Opzioni»)."""
    html(f'<div class="x-sec">{escape(text)}</div>')


def lead(text_html: str) -> None:
    """Frase di riepilogo in linguaggio semplice (l'HTML va già validato dal chiamante)."""
    html(f'<div class="x-lead">{text_html}</div>')


def hero(kicker: str, value: str, body_html: str = "", meta_html: Sequence[str] = (), nota_html: str = "",
         kicker_html: str = "", colore: str = "") -> None:
    """Testo del riquadro «Consiglio»: etichetta, verdetto e spiegazione.

    meta_html: righe sui dati usati, sotto il verdetto. nota_html: paragrafo sotto il verdetto (il perché del
    consiglio). kicker_html: accanto all'etichetta (la posizione stimata). colore: del verdetto, lo stesso del cerchio
    dello score (senza, il giallo AMBER del CSS). Gli HTML passati vanno già validati.
    """
    stile_v = f' style="color:{colore}"' if colore else ""
    meta = f'<span class="m">{"<br>".join(meta_html)}</span>' if meta_html else ""
    nota = f'<p class="x-hero-nota">{nota_html}</p>' if nota_html else ""
    html(f"""<div class="x-hero">
<div style="display:flex;flex-direction:column;gap:2px"><span class="k">{escape(kicker)}{kicker_html}</span>
<span class="v"{stile_v}>{escape(value)}</span>{meta}{nota}</div>
<p>{body_html}</p></div>""")


def hero_box(container):
    """Riquadro scuro «Consiglio» dentro `container`.

    Restituisce (colonna del testo, colonna a destra): a destra va il cerchio dello score. Il testo si scrive con
    hero(), che dentro il riquadro perde sfondo e ombra."""
    with container:
        with st.container(key="hero"):
            testo, lato = st.columns([1, 0.3], gap="medium", vertical_alignment="center")
    return testo, lato


def colore_score(esito: int) -> str:
    """Colore dello score del petrolio, per il cerchio e per il verdetto: rosso solo con -1 (Aspetta), verde gli altri."""
    return ROSSO if esito == -1 else VERDE


def cerchio_score(esito: int, etichetta: str) -> str:
    """Indicatore dello score del petrolio (HTML): cerchio bianco con bordo e simbolo colorati.

    +1 = freccia in su, 0 = pallino, -1 = freccia in giù; bordo e simbolo verdi, rossi solo con -1 (Aspetta). Il fondo
    bianco lo rende leggibile sul riquadro blu."""
    colore = colore_score(esito)
    if esito == 0:
        simbolo = f'<circle cx="32" cy="32" r="9" fill="{colore}"/>'
    else:
        punta, coda, ali = (18, 46, 30) if esito == 1 else (46, 18, 34)
        simbolo = (f'<path d="M32 {coda} V{punta} M20 {ali} L32 {punta} L44 {ali}" fill="none" stroke="{colore}" '
                   'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    return (f'<span class="x-cerchio" role="img" aria-label="{escape(etichetta)}" title="{escape(etichetta)}">'
            f'<svg width="64" height="64" viewBox="0 0 64 64" aria-hidden="true">'
            f'<circle cx="32" cy="32" r="28" fill="#fff" stroke="{colore}" stroke-width="5"/>{simbolo}</svg></span>')


def cerchio_progresso(pct: int, label: str = "", ritardo: bool = False) -> str:
    """Riquadro con cerchio SVG e progressione percentuale (0-100%)."""
    p = max(0, min(100, int(pct)))
    raggio = 44
    circ = 276.46
    offset = circ * (1.0 - p / 100.0)
    lbl_html = f'<div class="x-progress-lbl">{escape(label)}</div>' if label else ""
    return (
        f'<div class="x-progress-wrap{" x-ritardo" if ritardo else ""}" '
        f'role="status" aria-live="polite">'
        f'<div class="x-progress-box">'
        f'<svg width="110" height="110" viewBox="0 0 110 110">'
        f'<circle cx="55" cy="55" r="{raggio}" fill="none" stroke="{N200}" stroke-width="7"/>'
        f'<circle cx="55" cy="55" r="{raggio}" fill="none" stroke="{ORANGE}" stroke-width="7" '
        f'stroke-linecap="round" stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}" '
        f'transform="rotate(-90 55 55)" style="transition: stroke-dashoffset 0.1s ease-out;"/>'
        f'<text x="55" y="62" text-anchor="middle" font-size="20" font-weight="800" fill="{DEEP}">{p}%</text>'
        f'</svg>'
        f'{lbl_html}'
        f'</div></div>'
    )


def _avvia() -> None:
    st.session_state["avviato"] = True
    # il carburante scelto qui diventa quello della Home («_carburante», vedi ControlsView)
    if st.session_state.get("carburante_avvio"):
        st.session_state["_carburante"] = st.session_state["carburante_avvio"]


def avvio(carburanti: Sequence[str]) -> None:
    """Schermata d'avvio: il pulsante del distributore al centro fa partire posizione e download, poi si apre la Home.
    Sotto, il menu del carburante (la scelta passa a quello della Home)."""
    with st.container(key="avvio"):
        st.button(":material/local_gas_station:", key="avvia", help="Cerca la posizione e i prezzi di oggi", on_click=_avvia)
        html('<div class="x-progress-lbl">Tocca per trovare il distributore che conviene</div>')
        # il carburante salvato nel browser lo mette ui/preferenze.leggi nella chiave «carburante_avvio»
        st.selectbox("Carburante", carburanti, key="carburante_avvio", label_visibility="collapsed")


class Caricamento:
    """Il cerchio di caricamento unico, al centro dello schermo: avanza con dati MIMIT, Brent, score, posizione e
    distanze su strada, e si chiude in fondo ad app.py, a pagina completa.

    Copre sempre tutta la pagina con lo sfondo pieno (dietro non si vede la pagina a metà). Finché la Home non è mai
    stata mostrata (`st.session_state["pronta"]`) compare subito; nei ricalcoli dopo solo se l'attesa dura più di un
    attimo, così non lampeggia quando i dati sono già in memoria."""

    def __init__(self) -> None:
        self._posto = st.empty()
        self._inizio: float | None = None

    def mostra(self, pct: int, label: str, subito: bool = False) -> None:
        """`subito`: senza il ritardo dei ricalcoli, quando la pagina si ferma a metà (il resto sparirebbe)."""
        if self._inizio is None:
            self._inizio = time.monotonic()
        primo = not st.session_state.get("pronta")
        # nei ricalcoli, nei primi istanti compare con un attimo di ritardo: con i dati in memoria non si vede nemmeno
        ritardo = not (primo or subito) and time.monotonic() - self._inizio < 0.3
        self._posto.markdown(cerchio_progresso(pct, label, ritardo), unsafe_allow_html=True)

    def chiudi(self) -> None:
        self._posto.empty()
        self._inizio = None


def error_card(msg_html: str) -> None:
    """Riquadro d'errore; `msg_html` è HTML già pronto (le parti variabili vanno escapate da chi lo scrive)."""
    html(f'<div class="x-err">{msg_html}</div>')


def table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> None:
    """Tabella senza righe di separazione; le celle sono HTML già pronto."""
    th = "".join(f"<th>{h}</th>" for h in headers)
    tb = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    html(f'<div class="x-scroll"><table class="x-table"><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>')


def colophon() -> None:
    """Colofon a piè di pagina."""
    html('<div class="x-colophon" role="contentinfo">'
         '<span class="x-colophon-brand">sCore lab</span>'
         '<span class="x-colophon-ver">v1.0</span>'
         '<span class="x-colophon-dot">·</span>'
         '<span class="x-colophon-text">Tutti i diritti riservati</span>'
         '</div>')


# pagina di GitHub Pages (cartella docs/) con manifest e icone: mostra l'app a tutto schermo e si può installare
INSTALLA_URL = "https://saveriopititto-bot.github.io/refillo/"
_POMPA = ('<svg viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><path d="M19.77 7.23l.01-.01-3.72-3.72'
          'L15 4.56l2.11 2.11c-.94.36-1.61 1.26-1.61 2.33 0 1.38 1.12 2.5 2.5 2.5.36 0 .69-.08 1-.21v7.21c0 .55-.45 1-1 1'
          's-1-.45-1-1V14c0-1.1-.9-2-2-2h-1V5c0-1.1-.9-2-2-2H6c-1.1 0-2 .9-2 2v16h10v-7.5h1.5v5c0 1.38 1.12 2.5 2.5 2.5'
          's2.5-1.12 2.5-2.5V9c0-.69-.28-1.32-.73-1.77zM12 10H6V5h6v5zm6 0c-.55 0-1-.45-1-1s.45-1 1-1 1 .45 1 1-.45 1-1 1z'
          '"/></svg>')


def _chiudi_installa() -> None:
    # la scelta resta nel browser con le altre preferenze (ui/preferenze.py)
    st.session_state["installa_chiuso"] = True


def invito_installa() -> None:
    """Striscia in fondo alla Home, solo da telefono (CSS): porta alla pagina da cui si installa l'app."""
    with st.container(key="installa", horizontal=True):
        html(f'<div class="x-installa"><div class="x-installa-ic">{_POMPA}</div>'
             '<div class="x-installa-txt"><b>Installa Refillo</b>Aprila dalla schermata Home, come un\'app.</div></div>')
        st.link_button("Installa", INSTALLA_URL)
        st.button("×", key="installa_chiudi", help="Non mostrare più", on_click=_chiudi_installa)
