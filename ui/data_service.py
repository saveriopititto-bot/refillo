"""Servizi di dati, caching e geolocalizzazione per l'app Streamlit."""
from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit_js_eval

import fuel_model as fm
from ui.config import supabase_config
from ui.formatters import num

BASE = Path(__file__).resolve().parent.parent
ANAG_FILE, PREZZI_FILE = fm.ANAG_FILE, fm.PREZZI_FILE
CACHE_ORE = 3  # i prezzi MIMIT cambiano una volta al giorno
BRENT_GIORNI = 7  # n: finestra della variazione del Brent

GEO_ERRORI = {
    1: "hai negato il permesso di accedere alla posizione (puoi riattivarlo dalle impostazioni del sito nel browser)",
    2: "il dispositivo non riesce a determinare la posizione",
    3: "la richiesta di posizione è scaduta",
}

PERCHE_PETROLIO = {
    1: "Il petrolio costa più del solito. Tra pochi giorni anche il carburante costerà di più. Fai il pieno oggi.",
    0: "Il petrolio costa come al solito. La benzina non cambierà molto. Fai benzina quando ti serve.",
    -1: "Il petrolio costa meno del solito. Tra pochi giorni anche la benzina costerà di meno. Se puoi, aspetta.",
}


def default_path(name: str) -> Path | None:
    for d in (BASE / "data", BASE, Path.cwd()):
        if (d / name).exists():
            return d / name
    return None


@st.cache_data(max_entries=2, show_spinner="Leggo i CSV…")
def load_data(anag_bytes: bytes, prezzi_bytes: bytes) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp | None]:
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
    except Exception as e:
        return None, str(e) or type(e).__name__


@st.cache_data(ttl=CACHE_ORE * 3600, show_spinner="Leggo lo score del petrolio…")
def brent_score(url: str, chiave: str) -> tuple[dict | None, str]:
    """Ultimo score del Brent da Supabase; (None, motivo) se non raggiungibile. Anche l'errore resta in cache."""
    try:
        return fm.fetch_brent_score(url, chiave), ""
    except Exception as e:
        return None, str(e) or type(e).__name__


def leggi_brent_score() -> tuple[dict | None, str]:
    """Score del petrolio, oppure (None, motivo). Non configurato non va in cache."""
    url, chiave, nomi = supabase_config()
    if not (url and chiave):
        mancano = [n for n, v in (("SUPABASE_URL", url), ("SUPABASE_ANON_KEY", chiave)) if not v]
        trovati = ", ".join(nomi) if nomi else "nessuno"
        return None, f"non configurato|{', '.join(mancano)}|{trovati}"
    return brent_score(url, chiave)


def perche_petrolio(bs: dict) -> str:
    """Il perché del consiglio (HTML sicuro)."""
    return escape(PERCHE_PETROLIO[bs["esito"]])


def nota_score(motivo: str) -> str:
    """Spiega perché manca lo score del petrolio e il Consiglio usa il verdetto sul risparmio."""
    if motivo.startswith("non configurato|"):
        _, mancano, trovati = motivo.split("|", 2)
        return (f"Score del petrolio non configurato: nei Secrets di questa app su Streamlit manca "
                f"<code>{escape(mancano)}</code> (segreti trovati: <code>{escape(trovati)}</code>)")
    return f"Score del petrolio da Supabase non raggiungibile ({escape(motivo)})"


_CACHE_MIMIT: dict[str, tuple[bytes, pd.Timestamp]] = {}


def get_mimit_dataset(
    c_progress: any = None,
    up_a: any = None,
    up_p: any = None,
) -> tuple[tuple[bytes | None, str], tuple[bytes | None, str]]:
    """Carica o scarica anagrafica e prezzi MIMIT mostrando il cerchio con la percentuale."""
    import time
    import style

    if up_a is not None and up_p is not None:
        return (up_a.getvalue(), "caricato"), (up_p.getvalue(), "caricato")
    anag_b = up_a.getvalue() if up_a is not None else None
    prezzi_b = up_p.getvalue() if up_p is not None else None
    src_a = "caricato" if anag_b else ""
    src_p = "caricato" if prezzi_b else ""

    if anag_b is None:
        pa = default_path(ANAG_FILE)
        if pa:
            anag_b, src_a = pa.read_bytes(), "locale"
    if prezzi_b is None:
        pp = default_path(PREZZI_FILE)
        if pp:
            prezzi_b, src_p = pp.read_bytes(), "locale"

    if anag_b is not None and prezzi_b is not None:
        return (anag_b, src_a), (prezzi_b, src_p)

    ora = pd.Timestamp.now(tz="Europe/Rome")
    ttl_sec = CACHE_ORE * 3600

    def cache_valida(name: str) -> bytes | None:
        if name in _CACHE_MIMIT:
            data, ts = _CACHE_MIMIT[name]
            if (ora - ts).total_seconds() < ttl_sec:
                return data
        return None

    cached_a = cache_valida(ANAG_FILE) if anag_b is None else anag_b
    cached_p = cache_valida(PREZZI_FILE) if prezzi_b is None else prezzi_b

    if cached_a is not None and cached_p is not None:
        if ANAG_FILE in _CACHE_MIMIT:
            st.session_state["scaricato_alle"] = _CACHE_MIMIT[ANAG_FILE][1]
        return (cached_a, src_a or "scaricato"), (cached_p, src_p or "scaricato")

    st.session_state.pop("download_err", None)
    try:
        last_pct = [-1]

        def update_progress(pct: int, label: str):
            if c_progress is not None and pct != last_pct[0]:
                last_pct[0] = pct
                c_progress.markdown(style.cerchio_progresso(pct, label), unsafe_allow_html=True)

        update_progress(0, "Connessione ai server del MIMIT…")

        if cached_a is None:
            def on_anag(read: int, total: int):
                p = int((read / max(1, total)) * 50) if total else 25
                update_progress(p, "Scaricamento anagrafica impianti…")

            anag_bytes = fm.download_csv(ANAG_FILE, on_progress=on_anag)
            _CACHE_MIMIT[ANAG_FILE] = (anag_bytes, ora)
            cached_a = anag_bytes
            update_progress(50, "Anagrafica completata!")
        else:
            update_progress(50, "Anagrafica già disponibile…")

        if cached_p is None:
            def on_prezzi(read: int, total: int):
                p = 50 + (int((read / max(1, total)) * 50) if total else 25)
                update_progress(p, "Scaricamento prezzi dal MIMIT…")

            prezzi_bytes = fm.download_csv(PREZZI_FILE, on_progress=on_prezzi)
            _CACHE_MIMIT[PREZZI_FILE] = (prezzi_bytes, ora)
            cached_p = prezzi_bytes
            update_progress(100, "Dati MIMIT completati con successo!")
        else:
            update_progress(100, "Dati MIMIT completati!")

        time.sleep(0.15)
        st.session_state["scaricato_alle"] = ora
        return (cached_a, "scaricato"), (cached_p, "scaricato")

    except Exception as e:
        st.session_state.setdefault("download_err", []).append(f"{e}")
        return (None, ""), (None, "")


def get_bytes(uploaded, name: str) -> tuple[bytes | None, str]:
    """Contenuto del CSV e da dove arriva: caricato a mano, cartella data/ o download dal MIMIT."""
    if uploaded is not None:
        return uploaded.getvalue(), "caricato"
    p = default_path(name)
    if p:
        return p.read_bytes(), "locale"
    if name in _CACHE_MIMIT:
        data, ts = _CACHE_MIMIT[name]
        ora = pd.Timestamp.now(tz="Europe/Rome")
        if (ora - ts).total_seconds() < CACHE_ORE * 3600:
            st.session_state["scaricato_alle"] = ts
            return data, "scaricato"
    try:
        data, quando = download(name)
        _CACHE_MIMIT[name] = (data, quando)
    except Exception as e:
        st.session_state.setdefault("download_err", []).append(f"{name}: {e}")
        return None, ""
    st.session_state["scaricato_alle"] = quando
    return data, "scaricato"


def clear_all_caches() -> None:
    """Pulisce le cache Streamlit per riscaricare i dati."""
    _CACHE_MIMIT.clear()
    download.clear()
    brent_yahoo.clear()
    brent_score.clear()


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
