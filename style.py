"""Stile 'smooth' (opzione 1a, lo stesso di test4): CSS globale e blocchi HTML riusati da app.py."""
from __future__ import annotations

from collections.abc import Sequence
from html import escape

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
# colori dell'indicatore del petrolio (verde = sale, rosso = scende; il neutro usa ORANGE)
VERDE, ROSSO = "#1f9d55", "#d64545"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;800&display=swap');
:root {{ --radius-lg: 22px; --radius-md: 14px;
  --shadow-soft: 0 1px 2px rgba(2,48,71,.04), 0 10px 30px rgba(2,48,71,.07); }}
html, body, .stApp {{ font-family: 'Archivo', system-ui, sans-serif; }}
.stApp {{ background: {BG}; color: {DEEP}; }}
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

/* tab come barra di navigazione a pillole (selettori per Streamlit < 1.6x e >= 1.6x), sotto il riquadro «Consiglio» */
.stTabs [data-baseweb="tab-list"], .stTabs [role="tablist"] {{ gap: 4px; align-items: center; flex-wrap: wrap;
  row-gap: 10px; background: #fff; border: 0; box-shadow: var(--shadow-soft); padding: 12px 24px;
  border-radius: var(--radius-lg); overflow: visible; }}
.stTabs [data-baseweb="tab"], .stTabs [role="tab"] {{ height: auto; padding: 8px 10px; margin: 0; border: 0;
  border-radius: 999px; background: transparent; cursor: pointer; }}
.stTabs [role="tab"] p {{ font-size: 14px; font-weight: 600; color: {DEEP}; }}
.stTabs [role="tab"]:hover p {{ color: {ORANGE}; }}
.stTabs [role="tab"][aria-selected="true"] {{ background: {DEEP}; }}
.stTabs [role="tab"][aria-selected="true"] p {{ color: #fff; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"],
.stTabs .react-aria-SelectionIndicator, .stTabs [role="tablist"]::before,
.stTabs [role="tablist"]::after {{ display: none; }}
.stTabs [role="tabpanel"] {{ padding-top: 20px; }}

/* un solo riquadro bianco con le pillole e tutto il contenuto delle schede: la barra delle pillole e le
   schede interne perdono sfondo e ombra, gli indicatori diventano riquadri tenui */
.st-key-card-schede .stTabs [data-baseweb="tab-list"], .st-key-card-schede .stTabs [role="tablist"] {{
  background: transparent; box-shadow: none; padding: 0; border-radius: 0; }}
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
/* mappa Leaflet (cornice di components.html): quadrata, a qualunque larghezza dello schermo; al massimo 400 px di
   larghezza (400 × 400), centrata */
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
.st-key-hero [data-baseweb="select"] > div {{
  min-height: 36px !important; border-radius: 999px !important; padding: 0 6px !important;
}}
.st-key-hero [data-baseweb="select"] *,
.st-key-hero [data-testid="stSelectbox"] input {{
  font-size: 12.5px !important; font-weight: 700 !important; white-space: nowrap !important;
}}

/* blocchi HTML: Streamlit dà margin-bottom -16px al contenitore markdown */
[data-testid="stMarkdownContainer"]:has(> [class^="x-"]) {{ margin-bottom: 0; }}
.x-sec {{ font-size: 11px; letter-spacing: .1em; text-transform: uppercase; font-weight: 800; color: {N700};
  margin-top: 4px; }}
.x-lead {{ font-size: 15px; line-height: 1.45; text-align: justify; text-justify: inter-word; color: {DEEP}; }}
.x-lead strong {{ color: {A700}; }}
.x-lead-box {{ background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-soft); padding: 22px 26px;
  font-size: 19px; line-height: 1.5; text-wrap: pretty; }}
.x-lead-box strong {{ color: {A700}; }}
.x-label {{ font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: {N700}; }}
/* indicatori: riquadri compatti, sempre tutti su una riga */
.x-metrics {{ display: grid; grid-auto-flow: column; grid-auto-columns: minmax(0, 1fr); gap: 10px; }}
.x-metric {{ background: #fff; border-radius: var(--radius-md); box-shadow: var(--shadow-soft); padding: 10px 14px;
  display: flex; flex-direction: column; gap: 2px; min-width: 0; }}
.x-metric .x-label {{ font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.x-metric .v {{ font-size: 20px; font-weight: 800; letter-spacing: -.02em; line-height: 1.15; font-variant-numeric: tabular-nums;
  white-space: nowrap; }}
.x-metric .s {{ font-size: 12px; line-height: 1.3; color: {N700}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
@media (max-width: 640px) {{
  [class*="st-key-card-controls"] {{ padding: 14px 10px !important; }}
  /* da telefono margini minimi: pagina quasi a tutta larghezza e riquadri con poco bordo interno */
  [data-testid="stMainBlockContainer"] {{ padding: 4px 6px 4px !important; }}
  [class*="st-key-card"] {{ padding: 10px; }}
  .st-key-comandi [data-testid="stHorizontalBlock"] {{ gap: 4px !important; }}
  .st-key-comandi button {{ min-height: 32px !important; padding: 4px 2px !important; }}
  .st-key-comandi button p {{ font-size: 11.5px !important; }}
  .st-key-comandi button div[aria-hidden="true"]:has([data-testid="stIconMaterial"]) {{ display: none !important; }}
  /* niente freccia da telefono: c'è poco spazio */
  .st-key-hero [data-baseweb="select"] > div {{ min-height: 32px !important; padding: 0 4px !important; }}
  .st-key-hero [data-baseweb="select"] *,
  .st-key-hero [data-testid="stSelectbox"] input {{ font-size: 11px !important; }}
  .stButton button, .stDownloadButton button {{ padding: 6px 10px; min-height: 32px; }}
  .stButton button p, .stDownloadButton button p {{ font-size: 12px; font-weight: 700; }}
  [data-testid="stExpander"] summary {{ min-height: 32px; padding: 5px 10px; font-size: 12px; }}
  .stTabs [data-baseweb="tab-list"], .stTabs [role="tablist"] {{ padding: 8px 12px; gap: 4px; }}
  .st-key-card-schede {{ padding: 8px !important; }}
  .st-key-card-schede .stTabs [data-baseweb="tab-list"], .st-key-card-schede .stTabs [role="tablist"] {{ padding: 0; }}
  .stTabs [data-baseweb="tab"], .stTabs [role="tab"] {{ padding: 6px 8px; }}
  .stTabs [role="tab"] p {{ font-size: 12.5px; }}
  .x-metrics {{ gap: 6px; }}
  .x-metric {{ padding: 8px 8px; }}
  .x-metric {{ justify-content: space-between; }}
  .x-metric .x-label {{ font-size: 9px; letter-spacing: .03em; white-space: normal; line-height: 1.25; }}
  .x-metric .v {{ font-size: 13px; letter-spacing: -.03em; }}
  .x-metric .s {{ display: none; }}
}}
.x-hero {{ background: linear-gradient(135deg, {DEEP}, #04466a); color: #fff; border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft); padding: 16px 22px; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 8px 28px; align-items: center; }}
.x-hero .k {{ font-size: 10px; letter-spacing: .1em; text-transform: uppercase; font-weight: 600; color: {SKY}; }}
.x-hero .v {{ font-size: 26px; font-weight: 800; letter-spacing: -.03em; line-height: 1; color: {AMBER}; }}
.x-hero .s {{ font-size: 15px; font-weight: 600; }}
.x-hero .m {{ font-size: 12px; line-height: 1.4; color: {SKY}; margin: 2px 0; }}
.x-hero.wait .m {{ color: {A100}; }}
.x-hero.wait {{ background: linear-gradient(135deg, {A700}, {A600}); }}
.x-hero.wait .k {{ color: {A100}; }}
.x-hero.wait .v {{ color: #fff; }}
.x-hero p {{ margin: 0; font-size: 14px; line-height: 1.35; text-wrap: pretty; color: #fff; }}
.x-hero p.x-hero-nota {{ margin-top: 2px; color: {N200}; max-width: 62ch; }}
.x-cerchio {{ display: inline-flex; line-height: 0; filter: drop-shadow(0 2px 6px rgba(2,48,71,.25)); }}
.x-hero.aside {{ grid-template-columns: minmax(0, 1fr) auto; padding-right: 14px; }}
.x-hero-aside {{ display: flex; align-items: center; justify-content: flex-end; margin: -8px 0; }}
.x-hero-aside svg {{ width: 72px; height: 72px; }}
@media (max-width: 640px) {{ .x-hero-aside svg {{ width: 54px; height: 54px; }} }}
/* riquadro «Consiglio» con il testo a sinistra e, a destra, il cerchio dello score sopra il menu del carburante:
   le due colonne restano affiancate anche da telefono */
.st-key-hero {{ background: linear-gradient(135deg, {DEEP}, #04466a); color: #fff; border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft); padding: 12px 14px 12px 16px; }}
.st-key-hero [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: 16px !important; }}
.st-key-hero [data-testid="stColumn"]:first-child {{ flex: 1 1 0 !important; min-width: 0 !important; width: auto !important; }}
.st-key-hero [data-testid="stColumn"]:last-child {{ flex: 0 0 130px !important; min-width: 0 !important; width: auto !important; }}
.st-key-hero .x-hero {{ background: none; box-shadow: none; padding: 0; border-radius: 0; display: flex;
  flex-direction: column; align-items: stretch; gap: 4px; }}
.st-key-hero .x-hero-aside {{ justify-content: center; margin: 0 0 4px; }}
.st-key-hero .x-lead-box {{ background: none; box-shadow: none; padding: 0; color: #fff; font-size: 16px; }}
.st-key-hero .x-lead-box strong {{ color: {AMBER}; }}
.st-key-hero .x-note {{ color: {SKY}; }}
@media (max-width: 640px) {{
  .st-key-hero {{ padding: 8px 10px 8px 12px; }}
  .x-hero .v {{ font-size: 23px; }}
  .x-hero p {{ font-size: 13px; }}
  .x-lead {{ font-size: 14px; line-height: 1.4; }}
  [class*="st-key-card"] [data-testid="stCaptionContainer"] p {{ font-size: 10.5px; line-height: 1.25; }}
  .st-key-hero [data-testid="stHorizontalBlock"] {{ gap: 10px !important; }}
  /* menu del carburante più basso: è lui a decidere l'altezza del riquadro «Consiglio» */
  .st-key-hero [data-testid="stSelectbox"] [data-baseweb="select"] > div,
  .st-key-hero [data-testid="stSelectbox"] > div > div {{ min-height: 30px !important; }}
  .st-key-hero [data-testid="stSelectbox"] input,
  .st-key-hero [data-testid="stSelectbox"] button {{ height: 28px !important; min-height: 0 !important;
    padding-top: 0 !important; padding-bottom: 0 !important; }}
  .st-key-hero [data-testid="stColumn"]:last-child {{ flex-basis: 104px !important; }}
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

/* cerchio di caricamento / progressione */
.x-progress-wrap {{ display: flex; justify-content: center; align-items: center; padding: 24px 16px; width: 100%; }}
.x-progress-box {{ background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-soft);
  padding: 26px 32px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 14px; max-width: 360px; width: 100%; text-align: center; }}
.x-progress-lbl {{ font-size: 13px; font-weight: 700; color: {DEEP}; line-height: 1.35; letter-spacing: -0.01em; }}
@media (max-width: 640px) {{
  .x-progress-box {{ padding: 18px 20px; max-width: 290px; gap: 10px; }}
  .x-progress-box svg {{ width: 95px; height: 95px; }}
  .x-progress-lbl {{ font-size: 12px; }}
}}

/* colofon */
.x-colophon {{ display: flex; align-items: center; justify-content: center; gap: 8px; flex-wrap: wrap;
  padding: 2px 8px 0; font-size: 12px; color: {N700}; text-align: center; }}
.x-colophon-brand {{ font-weight: 800; letter-spacing: -0.015em; color: {DEEP}; }}
.x-colophon-ver {{ display: inline-flex; align-items: center; font-size: 11px; font-weight: 700;
  padding: 1px 7px; border-radius: 999px; background: {N200}; color: {BLUE_GREEN}; letter-spacing: .02em; }}
.x-colophon-dot {{ color: {N500}; }}
.x-colophon-text {{ color: {N700}; font-size: 12px; }}
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
    """Titoletto di sezione nella barra laterale."""
    html(f'<div class="x-sec">{escape(text)}</div>')


def lead(text_html: str) -> None:
    """Frase di riepilogo in linguaggio semplice (l'HTML va già validato dal chiamante)."""
    html(f'<div class="x-lead">{text_html}</div>')


def hero(kicker: str, value: str, sub: str, body_html: str, ok: bool = True,
         meta_html: Sequence[str] = (), aside_html: str = "", nota_html: str = "") -> None:
    """Scheda scura in evidenza con il verdetto (ambra se non conviene).

    meta_html: righe sui dati usati, tra il verdetto e il sottotitolo. aside_html: al posto del testo, un elemento
    allineato a destra e alto quanto la scheda (il cerchio dello score). nota_html: paragrafo sotto il
    sottotitolo, nella colonna di sinistra (il perché del consiglio). Gli HTML passati vanno già validati.
    """
    meta = f'<span class="m">{"<br>".join(meta_html)}</span>' if meta_html else ""
    nota = f'<p class="x-hero-nota">{nota_html}</p>' if nota_html else ""
    sottotitolo = f'<span class="s">{escape(sub)}</span>' if sub else ""
    classi = "x-hero" + ("" if ok else " wait") + (" aside" if aside_html else "")
    destra = f'<div class="x-hero-aside">{aside_html}</div>' if aside_html else f"<p>{body_html}</p>"
    html(f"""<div class="{classi}">
<div style="display:flex;flex-direction:column;gap:2px"><span class="k">{escape(kicker)}</span>
<span class="v">{escape(value)}</span>{meta}{sottotitolo}{nota}</div>
{destra}</div>""")


def hero_box(container):
    """Riquadro scuro «Consiglio» dentro `container`.

    Restituisce (colonna del testo, colonna a destra): a destra vanno il cerchio dello score e, sotto, il menu del
    carburante. Il testo si scrive con hero(), che dentro il riquadro perde sfondo e ombra."""
    with container:
        with st.container(key="hero"):
            testo, lato = st.columns([1, 0.3], gap="medium", vertical_alignment="center")
    return testo, lato


def cerchio_score(esito: int, etichetta: str) -> str:
    """Indicatore dello score del petrolio (HTML): cerchio bianco con bordo e simbolo colorati.

    +1 = bordo verde con freccia verde in su, -1 = bordo rosso con freccia rossa in giù, 0 = bordo arancione con
    pallino arancione. Il fondo bianco lo rende leggibile sia sul riquadro blu sia su quello ambra."""
    colore = {1: VERDE, 0: ORANGE, -1: ROSSO}[esito]
    if esito == 0:
        simbolo = f'<circle cx="32" cy="32" r="9" fill="{colore}"/>'
    else:
        punta, coda, ali = (18, 46, 30) if esito == 1 else (46, 18, 34)
        simbolo = (f'<path d="M32 {coda} V{punta} M20 {ali} L32 {punta} L44 {ali}" fill="none" stroke="{colore}" '
                   'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    return (f'<span class="x-cerchio" role="img" aria-label="{escape(etichetta)}" title="{escape(etichetta)}">'
            f'<svg width="64" height="64" viewBox="0 0 64 64" aria-hidden="true">'
            f'<circle cx="32" cy="32" r="28" fill="#fff" stroke="{colore}" stroke-width="5"/>{simbolo}</svg></span>')


def cerchio_progresso(pct: int, label: str = "") -> str:
    """Riquadro con cerchio SVG e progressione percentuale (0-100%)."""
    p = max(0, min(100, int(pct)))
    raggio = 44
    circ = 276.46
    offset = circ * (1.0 - p / 100.0)
    lbl_html = f'<div class="x-progress-lbl">{escape(label)}</div>' if label else ""
    return (
        f'<div class="x-progress-wrap">'
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


def error_card(msg: str) -> None:
    html(f'<div class="x-err">{escape(msg)}</div>')


def table(headers: Sequence[str], rows: Sequence[Sequence[str]], widths: dict[int, str] | None = None) -> None:
    """Tabella senza righe di separazione; le celle sono HTML già pronto."""
    widths = widths or {}
    th = "".join(f'<th style="width:{widths[i]}">{h}</th>' if i in widths else f"<th>{h}</th>"
                 for i, h in enumerate(headers))
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
