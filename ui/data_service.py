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


def get_bytes(uploaded, name: str) -> tuple[bytes | None, str]:
    """Contenuto del CSV e da dove arriva: caricato a mano, cartella data/ o download dal MIMIT."""
    if uploaded is not None:
        return uploaded.getvalue(), "caricato"
    p = default_path(name)
    if p:
        return p.read_bytes(), "locale"
    try:
        data, quando = download(name)
    except Exception as e:
        st.session_state.setdefault("download_err", []).append(f"{name}: {e}")
        return None, ""
    st.session_state["scaricato_alle"] = quando
    return data, "scaricato"


def clear_all_caches() -> None:
    """Pulisce le cache Streamlit per riscaricare i dati."""
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
