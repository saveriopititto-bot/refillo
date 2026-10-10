"""Stile 'smooth' (opzione 1a, lo stesso di test4): CSS globale e blocchi HTML riusati da app.py."""
from __future__ import annotations

from html import escape
from typing import Sequence

import streamlit as st

# palette
SKY = "#8ecae6"
BLUE_GREEN = "#219ebc"
DEEP = "#023047"
AMBER = "#ffb703"
ORANGE = "#fb8500"
# sfumature ricavate dalla palette
BG = "#eef6fa"
N100, N200, N300, N400, N500, N700 = "#f2f8fb", "#e2eef4", "#c9dde7", "#a5c2d1", "#7c9fb2", "#3a5f74"
A100, A600, A700 = "#fff3e6", "#e07600", "#a65600"

BRAND = "⛽ Score di rifornimento"
SIDEBAR_W = 290  # larghezza fissa della barra laterale (scheda + 20px di margine sinistro)

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
[data-testid="stMainBlockContainer"] {{ padding: 20px 20px 40px; max-width: none; }}
[data-testid="stMain"] [data-testid="stVerticalBlock"] {{ gap: 20px; }}

/* barra laterale: scheda bianca a larghezza fissa, alta quanto la finestra, senza scroll interno;
   20px di margine esterno = stesso spazio che separa le schede della pagina centrale */
section[data-testid="stSidebar"] {{ background: transparent; border: 0; }}
section[data-testid="stSidebar"][aria-expanded="true"] {{ width: {SIDEBAR_W}px !important;
  min-width: {SIDEBAR_W}px !important; max-width: {SIDEBAR_W}px !important; }}
section[data-testid="stSidebar"] > div {{ background: transparent; }}
section[data-testid="stSidebar"] div:has(> [data-testid="stSidebarResizeHandle"]) {{ display: none; }}
/* su schermi stretti la barra laterale si apre sopra la pagina: sfondo pieno attorno alla scheda */
@media (max-width: 767.98px) {{
  section[data-testid="stSidebar"][aria-expanded="true"] {{ background: {BG}; box-shadow: 0 0 40px rgba(2,48,71,.18); }}
}}
section[data-testid="stSidebar"] > [data-testid="stSidebarContent"] {{ background: #fff; border-radius: var(--radius-lg); margin: 20px 0 20px 20px;
  box-shadow: var(--shadow-soft); width: calc(100% - 20px) !important; height: calc(100vh - 40px);
  padding: 0; overflow-x: hidden; overflow-y: auto; position: relative; }}
[data-testid="stSidebarUserContent"] {{ padding: 12px 14px 10px; }}
[data-testid="stSidebarHeader"] {{ position: absolute; top: 12px; right: 12px; z-index: 2; padding: 0;
  height: auto; min-height: 0; width: auto; }}
[data-testid="stSidebarHeader"] [data-testid="stLogoSpacer"] {{ display: none; }}
/* barra laterale compatta: poco spazio tra i campi, campi e pulsanti bassi */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{ gap: 6px; }}
[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {{ gap: 8px; }}
[data-testid="stSidebar"] [data-baseweb="input"], [data-testid="stSidebar"] [data-testid="stNumberInputContainer"] {{
  height: 32px; }}
[data-testid="stSidebar"] [data-baseweb="select"] > div {{ min-height: 32px; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {{ min-height: 0; margin-bottom: 0; }}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] {{ gap: 0 12px; }}
[data-testid="stSidebar"] .stSlider {{ margin-top: -6px; margin-bottom: -8px; }}
[data-testid="stSidebar"] .stButton button, [data-testid="stSidebar"] .stDownloadButton button {{
  min-height: 32px; padding: 4px 14px; }}
[data-testid="stSidebar"] .stButton button p {{ font-size: 13px; }}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {{ padding: 8px 12px; }}
[data-testid="stSidebar"] [data-testid="stExpanderDetails"] {{ padding: 4px 12px 12px; }}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{ padding: 6px 8px; }}
[data-testid="stSidebar"] [data-testid="stFileUploaderDropzoneInstructions"] {{ display: none; }}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {{ font-size: 12px; color: {N700}; }}
[data-testid="stSidebar"] .stRadio [data-testid="stWidgetLabel"] p {{ font-size: 12px; font-weight: 800;
  letter-spacing: .08em; text-transform: uppercase; color: {N700}; }}
[data-testid="stSidebar"] .stRadio label p {{ font-size: 13px; color: {DEEP}; }}
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

/* tab come barra di navigazione (selettori per Streamlit < 1.6x e >= 1.6x) */
.stTabs [data-baseweb="tab-list"], .stTabs [role="tablist"] {{ gap: 4px; align-items: center; flex-wrap: wrap;
  row-gap: 10px; background: #fff; border: 0; box-shadow: var(--shadow-soft); padding: 12px 12px 12px 24px;
  border-radius: var(--radius-lg); overflow: visible; }}
.stTabs [data-baseweb="tab-list"]::before, .stTabs [role="tablist"]::before {{ content: "{BRAND}";
  margin-right: auto; padding-right: 16px; font-size: 18px; font-weight: 800; letter-spacing: -0.015em; color: {DEEP}; }}
.stTabs [data-baseweb="tab"], .stTabs [role="tab"] {{ height: auto; padding: 8px 10px; margin: 0; border: 0;
  border-radius: 999px; background: transparent; cursor: pointer; }}
.stTabs [role="tab"] p {{ font-size: 14px; font-weight: 600; color: {DEEP}; }}
.stTabs [role="tab"]:hover p {{ color: {ORANGE}; }}
.stTabs [role="tab"][aria-selected="true"] {{ background: {DEEP}; }}
.stTabs [role="tab"][aria-selected="true"] p {{ color: #fff; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"],
.stTabs .react-aria-SelectionIndicator, .stTabs [role="tablist"]::after {{ display: none; }}
.stTabs [role="tabpanel"] {{ padding-top: 20px; }}

/* schede */
[class*="st-key-card"] {{ position: relative; background: #fff; border: 1px solid transparent; border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft); padding: 24px; gap: 12px !important; }}
.x-title {{ margin: 0; font-size: 20px; line-height: 1.25; font-weight: 800; letter-spacing: -0.015em; color: {DEEP}; }}
[class*="st-key-card"] p {{ font-size: 14px; }}
.st-key-card-how p, .st-key-card-how li {{ font-size: 15px; line-height: 1.6; }}
[class*="st-key-card"] [data-testid="stCaptionContainer"] p {{ font-size: 13px; color: {N700}; }}
[class*="st-key-card"] [data-testid="stDeckGlJsonChart"], [class*="st-key-card"] [data-testid="stDataFrame"] {{
  border-radius: var(--radius-md); overflow: hidden; }}

/* bottoni */
.stButton button, .stDownloadButton button {{ border-radius: 999px; border: 0; padding: 10px 18px;
  font-weight: 800; min-height: 40px; }}
.stButton button p, .stDownloadButton button p {{ font-weight: 800; font-size: 14px; }}
.stButton button[kind="primary"] {{ background: {ORANGE}; color: {DEEP}; }}
.stButton button[kind="primary"]:hover {{ background: {A600}; color: {DEEP}; }}
.stButton button[kind="secondary"], .stDownloadButton button {{ background: {N200}; color: {DEEP}; }}
.stButton button[kind="secondary"]:hover, .stDownloadButton button:hover {{ background: {N300}; color: {DEEP}; }}

/* metriche di st.metric: riquadri tenui */
div[data-testid="stMetric"] {{ background: {N100}; border-radius: var(--radius-md); padding: 16px 20px; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] * {{ text-transform: uppercase !important; letter-spacing: .08em; font-size: 11px; color: {N700}; }}
div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] * {{ font-weight: 800; font-size: 26px; font-variant-numeric: tabular-nums; }}
[data-testid="stAlert"] {{ border-radius: var(--radius-md); border: 0; }}
[data-testid="stExpander"] details {{ border: 0; background: {N100}; border-radius: var(--radius-md); }}

/* blocchi HTML: Streamlit dà margin-bottom -16px al contenitore markdown */
[data-testid="stMarkdownContainer"]:has(> [class^="x-"]) {{ margin-bottom: 0; }}
.x-sec {{ font-size: 11px; letter-spacing: .1em; text-transform: uppercase; font-weight: 800; color: {N700};
  margin-top: 4px; }}
.x-lead {{ background: #fff; border-radius: var(--radius-lg); box-shadow: var(--shadow-soft); padding: 22px 26px;
  font-size: 19px; line-height: 1.5; text-wrap: pretty; }}
.x-lead strong {{ color: {A700}; }}
.x-label {{ font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: {N700}; }}
/* indicatori: riquadri compatti, sempre tutti su una riga */
.x-metrics {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }}
.x-metric {{ background: #fff; border-radius: var(--radius-md); box-shadow: var(--shadow-soft); padding: 10px 14px;
  display: flex; flex-direction: column; gap: 2px; min-width: 0; }}
.x-metric .x-label {{ font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.x-metric .v {{ font-size: 20px; font-weight: 800; letter-spacing: -.02em; line-height: 1.15; font-variant-numeric: tabular-nums;
  white-space: nowrap; }}
.x-metric .s {{ font-size: 12px; line-height: 1.3; color: {N700}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
@media (max-width: 640px) {{
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
.x-hero .v {{ font-size: 30px; font-weight: 800; letter-spacing: -.03em; line-height: 1; color: {AMBER}; }}
.x-hero .s {{ font-size: 15px; font-weight: 600; }}
.x-hero .m {{ font-size: 12px; line-height: 1.4; color: {SKY}; margin: 2px 0; }}
.x-hero.wait .m {{ color: {A100}; }}
.x-hero.wait {{ background: linear-gradient(135deg, {A700}, {A600}); }}
.x-hero.wait .k {{ color: {A100}; }}
.x-hero.wait .v {{ color: #fff; }}
.x-hero p {{ margin: 0; font-size: 14px; line-height: 1.45; text-wrap: pretty; color: #fff; }}
.x-err {{ background: {A100}; color: {A700}; font-weight: 600; border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft); padding: 20px 24px; }}
.x-tag {{ display: inline-flex; align-items: center; font-size: 11px; letter-spacing: .02em; padding: 3px 10px;
  border-radius: 999px; }}
.x-tag.accent {{ background: {A100}; color: #7a3f00; }}
.x-tag.neutral {{ background: {N100}; color: #1f4559; }}
.x-tag.outline {{ border: 1px solid {ORANGE}; color: {ORANGE}; }}
.x-scroll {{ overflow-x: auto; }}
.x-table, .x-table tr {{ border: 0; }}
.x-table {{ width: 100%; margin: 0; border-collapse: collapse; font-size: 14px; font-variant-numeric: tabular-nums; }}
.x-table th {{ text-align: left; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: {N700};
  padding: 8px; border: 0; font-weight: 400; background: transparent; }}
.x-table td {{ padding: 8px; border: 0; white-space: nowrap; }}
.x-table tbody tr:nth-child(odd) td {{ background: {N100}; }}
.x-table tbody tr td:first-child {{ border-radius: 10px 0 0 10px; font-weight: 600; }}
.x-table tbody tr td:last-child {{ border-radius: 0 10px 10px 0; }}
.stApp .x-note {{ font-size: 12px; line-height: 1.45; color: {N700}; margin: 0; }}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ font-size: 12px; line-height: 1.45; color: {N700}; }}
[data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stCaptionContainer"]) {{ margin-top: -6px; }}
[data-testid="stSidebar"] .x-note {{ font-size: 11px; }}
/* componente invisibile che chiede la posizione al browser: niente spazio vuoto */
[data-testid="stElementContainer"]:has(iframe[title^="streamlit_js_eval"]) {{ position: absolute; width: 0; height: 0;
  overflow: hidden; margin: 0; }}
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


def tag(text: str, kind: str = "accent") -> str:
    return f'<span class="x-tag {kind}">{escape(text)}</span>'


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
         meta_html: Sequence[str] = ()) -> None:
    """Scheda scura in evidenza con il verdetto (ambra se non conviene).

    meta_html: righe sui dati usati, tra il verdetto e il sottotitolo. body_html e meta_html vanno già validati.
    """
    meta = f'<span class="m">{"<br>".join(meta_html)}</span>' if meta_html else ""
    html(f"""<div class="x-hero{'' if ok else ' wait'}">
<div style="display:flex;flex-direction:column;gap:2px"><span class="k">{escape(kicker)}</span>
<span class="v">{escape(value)}</span>{meta}<span class="s">{escape(sub)}</span></div>
<p>{body_html}</p></div>""")


def error_card(msg: str) -> None:
    html(f'<div class="x-err">{escape(msg)}</div>')


def table(headers: Sequence[str], rows: Sequence[Sequence[str]], widths: dict[int, str] | None = None) -> None:
    """Tabella senza righe di separazione; le celle sono HTML già pronto."""
    widths = widths or {}
    th = "".join(f'<th style="width:{widths[i]}">{h}</th>' if i in widths else f"<th>{h}</th>"
                 for i, h in enumerate(headers))
    tb = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    html(f'<div class="x-scroll"><table class="x-table"><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>')
