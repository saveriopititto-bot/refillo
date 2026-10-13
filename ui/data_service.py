"""Servizi di dati, caching e geolocalizzazione per l'app Streamlit."""
from __future__ import annotations

from html import escape
from pathlib import Path
import time
from typing import Callable
import zlib

import pandas as pd
import streamlit as st
import streamlit_js_eval

import fuel_model as fm
from ui.config import supabase_config

BASE = Path(__file__).resolve().parent.parent
ANAG_FILE, PREZZI_FILE = fm.ANAG_FILE, fm.PREZZI_FILE
CACHE_ORE = 3  # i prezzi MIMIT cambiano una volta al giorno
BRENT_GIORNI = 7  # n: finestra della variazione del Brent

PERCHE_PETROLIO = {
    1: "Il petrolio costa più del solito. Tra pochi giorni anche il carburante costerà di più. Fai il pieno oggi.",
    0: "Il petrolio costa come al solito. Il carburante non cambierà molto. Fai il pieno quando ti serve.",
    -1: "Il petrolio costa meno del solito. Tra pochi giorni anche il carburante costerà di meno. Se puoi, aspetta.",
}


def default_path(name: str) -> Path | None:
    for d in (BASE / "data", BASE, Path.cwd()):
        if (d / name).exists():
            return d / name
    return None


def impronta(anag_bytes: bytes, prezzi_bytes: bytes) -> tuple[int, int, int, int]:
    """Chiave corta dei due CSV (lunghezza e CRC32, pochi ms): Streamlit non deve rileggere 7 MB a ogni tocco."""
    return len(anag_bytes), zlib.crc32(anag_bytes), len(prezzi_bytes), zlib.crc32(prezzi_bytes)


# cache_resource: le tabelle restano in memoria senza essere copiate a ogni giro (nessuno le modifica)
@st.cache_resource(max_entries=2, show_spinner=False)
def _load_data(_anag_bytes: bytes, _prezzi_bytes: bytes, chiave: tuple) -> tuple[pd.DataFrame, pd.DataFrame,
                                                                                  pd.Timestamp | None]:
    anag, extraction = fm.parse_anagrafica(_anag_bytes)
    # via i distributori con coordinate in conflitto con il loro comune (quanti sono: anag.attrs["esclusi"])
    sospette = fm.coordinate_sospette(anag)
    anag = anag[~sospette].reset_index(drop=True)
    anag.attrs["esclusi"] = int(sospette.sum())
    prezzi = fm.parse_prezzi(_prezzi_bytes)
    return anag, prezzi, extraction


def load_data(anag_bytes: bytes, prezzi_bytes: bytes) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp | None]:
    return _load_data(anag_bytes, prezzi_bytes, impronta(anag_bytes, prezzi_bytes))


@st.cache_resource(max_entries=16, show_spinner=False)
def candidati(_anag: pd.DataFrame, _prezzi: pd.DataFrame, chiave: tuple, fuel: str, self_service: bool,
              max_age: float, extraction: pd.Timestamp | None) -> pd.DataFrame:
    """Distributori validi per carburante e opzioni, in memoria (`chiave` = impronta dei CSV): compute_edges li copia."""
    return fm.build_candidates(_anag, _prezzi, fuel, self_service, max_age, extraction)


@st.cache_data(ttl=CACHE_ORE * 3600, show_spinner=False)
def brent_yahoo(n_giorni: int) -> tuple[dict | None, str]:
    """Brent ed EUR/USD da Yahoo Finance; in caso di errore (None, motivo), così anche il fallimento resta in cache."""
    try:
        return fm.fetch_brent_yf(n_giorni), ""
    except Exception as e:
        return None, str(e) or type(e).__name__


@st.cache_data(ttl=CACHE_ORE * 3600, show_spinner=False)
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
_FONTE_MIMIT: dict[str, str] = {}  # da dove arriva ogni file scaricato
FONTE_DATI, FONTE_SITO = "dalla copia GitHub (branch dati)", "dal sito del MIMIT"


def fonte_download() -> str:
    """Da dove sono stati scaricati i due file, in parole semplici (vuoto se non si sa)."""
    a, p = _FONTE_MIMIT.get(ANAG_FILE, ""), _FONTE_MIMIT.get(PREZZI_FILE, "")
    return a if a == p else f"(anagrafica {a or '?'}, prezzi {p or '?'})"


def ultimo_rilascio_mimit(ora: pd.Timestamp) -> pd.Timestamp:
    """Restituisce il punto di riferimento delle ore 09:00 più recente (oggi se ora >= 09:00, altrimenti ieri)."""
    rilascio_oggi = ora.floor("D") + pd.Timedelta(hours=9)
    return rilascio_oggi if ora >= rilascio_oggi else rilascio_oggi - pd.Timedelta(days=1)


def is_fresco_mimit(ts: pd.Timestamp, ora: pd.Timestamp) -> bool:
    """I dati MIMIT sono freschi se scaricati dopo l'ultimo rilascio delle 09:00."""
    return ts >= ultimo_rilascio_mimit(ora)


def dati_freschi(data: bytes, ora: pd.Timestamp) -> bool:
    """La copia del branch `dati` vale se è quella dell'ultimo rilascio delle 9:00.

    Il MIMIT data i file con il giorno prima («Estrazione del 10» nei file pubblicati l'11 mattina),
    come in build_candidates: la copia vale se estrazione + 1 giorno è il giorno dell'ultimo rilascio."""
    estrazione = fm._extraction_date(data[:200].decode("utf-8-sig", errors="replace").split("\n", 1)[0])
    if estrazione is None:
        return False
    return estrazione + pd.Timedelta(days=1) >= ultimo_rilascio_mimit(ora).tz_localize(None).normalize()


def get_mimit_dataset(
    progresso: Callable[[int, str], None] | None = None,
    up_a: any = None,
    up_p: any = None,
) -> tuple[tuple[bytes | None, str], tuple[bytes | None, str]]:
    """Carica o scarica anagrafica e prezzi MIMIT; `progresso(percentuale, testo)` fa avanzare il cerchio."""
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

    def cache_valida(name: str) -> bytes | None:
        if name in _CACHE_MIMIT:
            data, ts = _CACHE_MIMIT[name]
            if is_fresco_mimit(ts, ora):
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
            if progresso is not None and pct != last_pct[0]:
                last_pct[0] = pct
                progresso(pct, label)

        update_progress(0, "Connessione ai server del MIMIT…")

        def scarica(name: str, da: int, etichetta: str) -> bytes:
            """Copia del branch `dati` se è di oggi, altrimenti il sito MIMIT; avanza il cerchio da `da` a `da` + 50."""
            def on_progress(read: int, total: int):
                update_progress(da + (min(50, int(read / total * 50)) if total else 25), etichetta)

            try:
                data = fm.download_dati(name, on_progress=on_progress)
                if dati_freschi(data, ora):
                    _FONTE_MIMIT[name] = FONTE_DATI
                    return data
            except Exception:
                pass  # copia non raggiungibile: si scarica dal MIMIT
            data = fm.download_csv(name, on_progress=on_progress)
            _FONTE_MIMIT[name] = FONTE_SITO
            return data

        if cached_a is None:
            cached_a = scarica(ANAG_FILE, 0, "Scaricamento anagrafica impianti…")
            _CACHE_MIMIT[ANAG_FILE] = (cached_a, ora)
            update_progress(50, "Anagrafica completata!")
        else:
            update_progress(50, "Anagrafica già disponibile…")

        if cached_p is None:
            cached_p = scarica(PREZZI_FILE, 50, "Scaricamento prezzi dal MIMIT…")
            _CACHE_MIMIT[PREZZI_FILE] = (cached_p, ora)
            update_progress(100, "Dati MIMIT completati con successo!")
        else:
            update_progress(100, "Dati MIMIT completati!")

        time.sleep(0.15)
        st.session_state["scaricato_alle"] = ora
        return (cached_a, "scaricato"), (cached_p, "scaricato")

    except Exception as e:
        st.session_state.setdefault("download_err", []).append(f"{e}")
        return (None, ""), (None, "")


def clear_all_caches() -> None:
    """Pulisce le cache Streamlit per riscaricare i dati."""
    _CACHE_MIMIT.clear()
    _FONTE_MIMIT.clear()
    brent_yahoo.clear()
    brent_score.clear()


# Ripiego quando né il GPS né l'indirizzo internet danno una posizione in Italia.
ROMA = (41.9028, 12.4964)

# Posizione approssimativa dall'indirizzo internet (IP), chiesta dal browser di chi usa l'app (dal server si vedrebbe
# l'IP di Streamlit Cloud): geojs.io, poi ipwho.is; servizi gratuiti, senza chiave, con CORS. Massimo 4 secondi.
_IP_JS = """(async () => {
  const prova = async (url, f) => {
    const ac = new AbortController(); const t = setTimeout(() => ac.abort(), 4000);
    try { const r = await fetch(url, {signal: ac.signal}); if (!r.ok) throw new Error('HTTP ' + r.status); return f(await r.json()); }
    finally { clearTimeout(t); }
  };
  const da = d => ({lat: Number(d.latitude), lon: Number(d.longitude), citta: d.city || '', paese: d.country_code || ''});
  try { return await prova('https://get.geojs.io/v1/ip/geo.json', da); }
  catch (e) { try { return await prova('https://ipwho.is/', da); } catch (e2) { return {errore: String(e2)}; } }
})()"""

NOTA_PRECISA = ("Posizione stimata dalla rete (o Roma se non si riesce): per quella esatta consenti la posizione "
                "nel browser o scegli un comune in «Opzioni».")


def origine_da_ip(dato) -> tuple[tuple[float, float], str]:
    """Dal risultato della richiesta IP: ((lat, lon), nota). Fuori dall'Italia o in errore: Roma."""
    if isinstance(dato, dict) and "errore" not in dato:
        try:
            lat, lon = float(dato["lat"]), float(dato["lon"])
        except (KeyError, TypeError, ValueError):
            lat = lon = float("nan")
        la0, la1, lo0, lo1 = fm.ITALY_BBOX
        if la0 <= lat <= la1 and lo0 <= lon <= lo1:
            return (lat, lon), f"{dato.get('citta') or 'Posizione'} (stima)"
    return ROMA, "Roma (ripiego)"


def posizione_ip() -> tuple[tuple[float, float], str] | None:
    """Posizione dall'indirizzo internet, chiesta una volta per sessione; None mentre il browser risponde."""
    if "pos_ip" not in st.session_state:
        dato = streamlit_js_eval.streamlit_js_eval(js_expressions=_IP_JS, key="geo_ip")
        if dato is None:
            return None
        st.session_state["pos_ip"] = origine_da_ip(dato)
    return st.session_state["pos_ip"]


# GPS del browser con un tempo massimo: se chi usa l'app non risponde alla richiesta del permesso (o il GPS non trova
# la posizione) dopo 15 secondi vale come errore e si passa all'indirizzo internet. getLocation() è la funzione di
# streamlit_js_eval (la stessa di get_geolocation), che risponde {coords: …} oppure {error: {code, message}}.
GPS_ATTESA_S = 15
_GPS_JS = (f"Promise.race([getLocation(), new Promise(r => setTimeout(() => r({{error: {{code: 3, "
           f"message: 'timeout'}}}}), {GPS_ATTESA_S * 1000}))])")


def posizione_browser() -> tuple[tuple[float, float] | None, bool]:
    """Posizione reale dal browser (API Geolocation): ((lat, lon), True); (None, True) se il GPS ha risposto con un
    errore (negato, spento, tempo scaduto); (None, False) finché il browser non ha risposto."""
    giro = st.session_state.get("geo_giro", 0)
    geo = streamlit_js_eval.streamlit_js_eval(js_expressions=_GPS_JS, key=f"geo_{giro}")
    if not geo:
        return None, False
    c = geo.get("coords") if isinstance(geo, dict) else None
    if isinstance(c, dict):
        try:
            return (float(c["latitude"]), float(c["longitude"])), True
        except (KeyError, TypeError, ValueError):
            pass
    return None, True


def rileva_posizione() -> tuple[tuple[float, float] | None, str]:
    """Posizione da usare: prima il GPS; solo se fallisce (negato, spento, 15 secondi senza risposta) l'indirizzo
    internet, o Roma. ((lat, lon), nota) con nota vuota per il GPS; (None, "") mentre il browser risponde.

    Si chiama in cima ad app.py, già nella schermata d'avvio: la richiesta parte appena si apre l'app."""
    origin, risposto = posizione_browser()
    if origin is not None:
        return origin, ""
    if not risposto:  # il GPS non ha ancora risposto
        return None, ""
    da_ip = posizione_ip()
    return da_ip if da_ip is not None else (None, "")
