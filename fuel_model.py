"""Modello di scoring razionale per il rifornimento.

Calcola il peso degli archi dal nodo centrale (posizione della macchina)
verso i distributori vicini, a partire dai CSV open data MIMIT
(anagrafica impianti + prezzi alle 8).

    S_i = q * [ (P_market - P_i) + alpha * P_market * dB ] - D_i * C_km

    q   = litri acquistati (default V_tot * (1 - L))
    dB  = (B_t - B_{t-n}) / B_{t-n}, in euro, limitato a +-10%
    D_i = deviazione chilometrica (andata/ritorno, oppure detour rispetto
          alla rotta origine -> destinazione)
    C_km = consumo/100 * P_market + usura
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import requests

EARTH_RADIUS_KM = 6371.0088

# Solo i prodotti "standard": le varianti premium (Blue Diesel, V-Power, ...)
# hanno prezzi diversi e falserebbero il confronto.
FUELS = ("Benzina", "Gasolio", "GPL", "Metano")

# Intervalli plausibili (€/l, Metano €/kg) per scartare errori di inserimento.
PRICE_BOUNDS = {
    "Benzina": (0.8, 3.5),
    "Gasolio": (0.8, 3.5),
    "GPL": (0.3, 2.0),
    "Metano": (0.8, 3.5),
}

ITALY_BBOX = (35.0, 48.0, 6.0, 19.0)  # lat_min, lat_max, lon_min, lon_max

# Open data MIMIT, aggiornati ogni giorno (prezzi comunicati entro le 8).
MIMIT_URL = "https://www.mimit.gov.it/images/exportCSV/{name}"
ANAG_FILE = "anagrafica_impianti_attivi.csv"
PREZZI_FILE = "prezzo_alle_8.csv"


# --------------------------------------------------------------------------
# Lettura dei CSV
# --------------------------------------------------------------------------
def download_csv(name: str, timeout: float = 60.0) -> bytes:
    """Scarica uno dei CSV open data MIMIT (ANAG_FILE o PREZZI_FILE).

    Solleva ValueError se la risposta non sembra il CSV atteso (es. una pagina HTML d'errore).
    """
    from urllib.request import Request, urlopen

    req = Request(MIMIT_URL.format(name=name), headers={"User-Agent": "Mozilla/5.0 (score-rifornimento)"})
    with urlopen(req, timeout=timeout) as r:
        data = r.read()
    head = data[:2000].decode("utf-8-sig", errors="replace")
    if "|" not in head or head.lstrip().lower().startswith(("<!doctype", "<html")):
        raise ValueError(f"{name}: risposta non valida dal sito MIMIT")
    return data


def _to_text(src) -> str:
    if isinstance(src, (str, Path)):
        return Path(src).read_text(encoding="utf-8-sig", errors="replace")
    if isinstance(src, (bytes, bytearray)):
        return bytes(src).decode("utf-8-sig", errors="replace")
    data = src.read()
    return data.decode("utf-8-sig", errors="replace") if isinstance(data, bytes) else data


def _extraction_date(first_line: str) -> pd.Timestamp | None:
    m = re.search(r"(\d{4}-\d{2}-\d{2})", first_line)
    return pd.Timestamp(m.group(1)) if m else None


def parse_anagrafica(src) -> tuple[pd.DataFrame, pd.Timestamp | None]:
    """Legge anagrafica_impianti_attivi.csv (separatore '|', 1ª riga = titolo).

    Alcune righe hanno un '|' in più dentro nome/indirizzo: i campi fissi
    (id, gestore, bandiera, tipo in testa; comune, provincia, lat, lon in coda)
    permettono di ricostruirle senza perderle.
    """
    lines = _to_text(src).splitlines()
    extraction = _extraction_date(lines[0]) if lines else None
    rows = []
    for line in lines[2:]:
        f = line.split("|")
        if len(f) < 10:
            continue
        mid = f[4:-4]
        rows.append(
            (
                f[0].strip(),
                f[1].strip(),
                f[2].strip(),
                f[3].strip(),
                mid[0].strip() if mid else "",
                " ".join(m.strip() for m in mid[1:]),
                f[-4].strip().upper(),
                f[-3].strip().upper(),
                f[-2],
                f[-1],
            )
        )
    df = pd.DataFrame(
        rows,
        columns=["id", "gestore", "bandiera", "tipo", "nome", "indirizzo",
                 "comune", "provincia", "lat", "lon"],
    )
    for c in ("lat", "lon"):
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    la0, la1, lo0, lo1 = ITALY_BBOX
    df = df.dropna(subset=["lat", "lon"])
    df = df[df.lat.between(la0, la1) & df.lon.between(lo0, lo1)]
    return df.drop_duplicates("id").reset_index(drop=True), extraction


def parse_prezzi(src) -> pd.DataFrame:
    """Legge prezzo_alle_8.csv (separatore '|', 1ª riga = titolo)."""
    import io

    text = _to_text(src)
    df = pd.read_csv(io.StringIO(text), sep="|", skiprows=1, dtype=str, on_bad_lines="skip")
    df = df.rename(
        columns={"idImpianto": "id", "descCarburante": "carburante", "isSelf": "is_self", "dtComu": "dt_comu"}
    )
    df["id"] = df["id"].str.strip()
    df["carburante"] = df["carburante"].str.strip()
    df["prezzo"] = pd.to_numeric(df["prezzo"].str.replace(",", ".", regex=False), errors="coerce")
    df["is_self"] = pd.to_numeric(df["is_self"], errors="coerce").fillna(0).astype(int) == 1
    df["dt_comu"] = pd.to_datetime(df["dt_comu"], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    return df.dropna(subset=["prezzo"]).reset_index(drop=True)


def build_candidates(
    anag: pd.DataFrame,
    prezzi: pd.DataFrame,
    fuel: str,
    self_service: bool,
    max_age_days: float | None,
    extraction_date: pd.Timestamp | None,
) -> pd.DataFrame:
    """Un record per distributore: anagrafica + prezzo del carburante scelto."""
    p = prezzi[(prezzi.carburante.str.lower() == fuel.lower()) & (prezzi.is_self == self_service)]
    lo, hi = PRICE_BOUNDS.get(fuel, (0.0, 10.0))
    p = p[p.prezzo.between(lo, hi)]
    if max_age_days is not None and extraction_date is not None:
        limite = extraction_date + pd.Timedelta(days=1) - pd.Timedelta(days=max_age_days)
        p = p[p.dt_comu >= limite]
    p = p.sort_values("dt_comu").drop_duplicates("id", keep="last")
    out = anag.merge(p[["id", "prezzo", "dt_comu"]], on="id", how="inner")
    if extraction_date is not None:
        out["eta_giorni"] = (extraction_date + pd.Timedelta(days=1) - out["dt_comu"]).dt.total_seconds() / 86400
    return out.reset_index(drop=True)


# --------------------------------------------------------------------------
# Geometria
# --------------------------------------------------------------------------
def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


# --------------------------------------------------------------------------
# Brent
# --------------------------------------------------------------------------
def brent_delta(b_t, b_tn, eurusd_t=1.0, eurusd_tn=1.0, clip=0.10) -> float:
    """Variazione relativa del Brent in euro, limitata a +-clip.

    b_* in USD/barile; eurusd_* = dollari per 1 euro (quotazione EUR/USD).
    """
    e_t, e_tn = b_t / eurusd_t, b_tn / eurusd_tn
    return float(np.clip((e_t - e_tn) / e_tn, -clip, clip))


def fetch_brent_yf(n_days: int) -> dict:
    """Scarica Brent (BZ=F) ed EUR/USD da Yahoo Finance. Richiede `yfinance`."""
    import yfinance as yf

    start = pd.Timestamp.today().normalize() - pd.Timedelta(days=int(n_days) + 15)

    def serie(ticker: str) -> pd.Series:
        s = yf.Ticker(ticker).history(start=start)["Close"].dropna()
        if s.empty:
            raise ValueError(f"Nessun dato per {ticker}")
        s.index = s.index.tz_localize(None).normalize()
        return s

    def valore_a(s: pd.Series, giorno: pd.Timestamp) -> float:
        s = s[s.index <= giorno]
        if s.empty:
            raise ValueError("Storico insufficiente")
        return float(s.iloc[-1])

    brent, fx = serie("BZ=F"), serie("EURUSD=X")
    t = min(brent.index[-1], fx.index[-1])
    tn = t - pd.Timedelta(days=int(n_days))
    return {
        "data_t": t, "data_tn": tn,
        "b_t": valore_a(brent, t), "b_tn": valore_a(brent, tn),
        "fx_t": valore_a(fx, t), "fx_tn": valore_a(fx, tn),
    }


# --------------------------------------------------------------------------
# Score del Brent (app «Prezzo del petrolio», tabella brent_score in Supabase)
# --------------------------------------------------------------------------
BRENT_SCORE_TABELLA = "brent_score"
# esito -> (etichetta, spiegazione); +1 = il Brent è sopra la media dei 30 giorni più del normale
BRENT_SCORE_TESTI = {
    1: ("Conviene", "Il petrolio è sopra la sua media degli ultimi 30 giorni più del solito: i prezzi alla "
                    "pompa tendono a seguirlo con qualche giorno di ritardo, quindi conviene non aspettare."),
    0: ("Rifornisci", "Il petrolio è vicino alla sua media degli ultimi 30 giorni: per ora non spinge i prezzi "
                      "alla pompa né in su né in giù."),
    -1: ("Aspetta", "Il petrolio è sotto la sua media degli ultimi 30 giorni più del solito: i prezzi alla pompa "
                    "tendono a scendere nei prossimi giorni, quindi se puoi conviene aspettare."),
}


def fetch_brent_score(url: str, chiave: str, timeout: float = 15) -> dict:
    """Ultimo score del Brent dalla tabella brent_score di Supabase, letta con la chiave pubblica (anon).

    Restituisce data (giorno di borsa), esito (+1 rifornisci, 0 neutro, -1 aspetta), score, brent_eur,
    media_30_eur (euro al barile) e aggiornato_il. Solleva un'eccezione se la tabella è vuota o la risposta
    non è valida."""
    r = requests.get(
        f"{url.rstrip('/')}/rest/v1/{BRENT_SCORE_TABELLA}",
        params={"select": "data,esito,score,brent_eur,media_30_eur,aggiornato_il", "order": "data.desc",
                "limit": "1"},
        headers={"apikey": chiave, "Accept": "application/json"},
        timeout=timeout,
    )
    if r.status_code != 200:
        raise ValueError(f"Supabase ha risposto {r.status_code}")
    righe = r.json()
    if not righe:
        raise ValueError("la tabella brent_score è vuota")
    riga = righe[0]
    esito = int(riga["esito"])
    if esito not in BRENT_SCORE_TESTI:
        raise ValueError(f"esito non valido: {esito}")
    return {
        "data": pd.Timestamp(riga["data"]),
        "esito": esito,
        "score": float(riga["score"]),
        "brent_eur": float(riga["brent_eur"]),
        "media_30_eur": float(riga["media_30_eur"]),
        "aggiornato_il": pd.Timestamp(riga["aggiornato_il"]),
    }


# --------------------------------------------------------------------------
# Modello
# --------------------------------------------------------------------------
class ModelParams:
    def __init__(self,
                 v_tot: float = 50.0,
                 livello: float = 0.25,
                 litri: float | None = None,
                 alpha: float = 0.2,
                 delta_brent: float = 0.0,
                 consumo_l100: float = 5.0,
                 usura_eur_km: float = 0.05,
                 road_factor: float = 1.3,
                 raggio_km: float = 20.0,
                 use_osrm: bool = True,
                 ref_mode: str = "mediana",
                 theta: float = 0.0,
                 livello_min: float = 0.10):
        self.v_tot = v_tot
        self.livello = livello
        self.litri = litri
        self.alpha = alpha
        self.delta_brent = delta_brent
        self.consumo_l100 = consumo_l100
        self.usura_eur_km = usura_eur_km
        self.road_factor = road_factor
        self.raggio_km = raggio_km
        self.use_osrm = use_osrm
        self.ref_mode = ref_mode
        self.theta = theta
        self.livello_min = livello_min

    @property
    def litri_effettivi(self) -> float:
        cap = self.v_tot * (1 - self.livello)
        return cap if self.litri is None else float(min(self.litri, cap))


OSRM_URL = "https://router.project-osrm.org"


@lru_cache(maxsize=512)
def _osrm_table(origin: tuple[float, float], destinations: tuple[tuple[float, float], ...]) -> tuple:
    """Distanze stradali (km) dall'origine; solleva un'eccezione se OSRM non risponde, così l'errore non va in cache."""
    coords = ";".join(f"{lon:.5f},{lat:.5f}" for lat, lon in (origin, *destinations))  # OSRM vuole lon,lat
    resp = requests.get(f"{OSRM_URL}/table/v1/driving/{coords}",
                        params={"sources": "0", "annotations": "distance"}, timeout=5)
    if resp.status_code != 200:
        raise ValueError(f"OSRM ha risposto {resp.status_code}")
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("distances"):
        raise ValueError(f"OSRM: {data.get('code')}")
    # la prima riga contiene le distanze dall'origine a tutti i punti
    return tuple(d / 1000.0 if d is not None else None for d in data["distances"][0][1:])


@lru_cache(maxsize=256)
def _osrm_route(origin: tuple[float, float], dest: tuple[float, float]) -> tuple:
    coords = f"{origin[1]:.5f},{origin[0]:.5f};{dest[1]:.5f},{dest[0]:.5f}"
    resp = requests.get(f"{OSRM_URL}/route/v1/driving/{coords}",
                        params={"geometries": "geojson", "overview": "full"}, timeout=3)
    if resp.status_code != 200:
        raise ValueError(f"OSRM ha risposto {resp.status_code}")
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(f"OSRM: {data.get('code')}")
    return tuple(tuple(c) for c in data["routes"][0]["geometry"]["coordinates"])


def _arrotonda(punto) -> tuple[float, float]:
    # 5 decimali (circa 1 m): gli stessi dell'URL, così le richieste uguali riusano la cache
    return round(float(punto[0]), 5), round(float(punto[1]), 5)


def get_osrm_distances(origin: tuple[float, float], destinations: list[tuple[float, float]]) -> list[float | None]:
    """Distanze stradali in km dall'API pubblica di OSRM (max 99 destinazioni); None dove non disponibili.

    Le risposte riuscite restano in memoria: cambiare litri, consumo o soglie non rifà la richiesta."""
    if not destinations:
        return []
    try:
        return list(_osrm_table(_arrotonda(origin), tuple(_arrotonda(d) for d in destinations)))
    except Exception as e:
        print(f"Errore OSRM: {e}")
        return [None] * len(destinations)


def get_osrm_route(origin: tuple[float, float], dest: tuple[float, float]) -> list[list[float]]:
    """Geometria del percorso reale (GeoJSON: lista di [lon, lat]) dal server OSRM; [] se non disponibile."""
    try:
        return [list(c) for c in _osrm_route(_arrotonda(origin), _arrotonda(dest))]
    except Exception as e:
        print(f"Errore OSRM route: {e}")
        return []


def compute_edges(
    cands: pd.DataFrame,
    origin: tuple[float, float],
    p: ModelParams,
    dest: tuple[float, float] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Pesi degli archi origine -> distributore.

    Restituisce (tabella ordinata per score decrescente, riepilogo).
    Colonne chiave: score = S_i (da massimizzare), peso = -S_i (costo per
    cammino minimo), peso_pos = S_max - S_i (costo non negativo).
    """
    olat, olon = origin
    df = cands.copy()
    df["dist_km"] = haversine_km(olat, olon, df.lat.values, df.lon.values) * p.road_factor
    df = df[df.dist_km <= p.raggio_km].copy()
    
    if getattr(p, "use_osrm", True) and not df.empty:
        # Prendi i 99 più vicini per rispettare i limiti di OSRM (1 origin + 99 dest = 100)
        cands_idx = df.nsmallest(99, "dist_km").index
        dests = list(zip(df.loc[cands_idx, "lat"], df.loc[cands_idx, "lon"]))
        
        real_dists = get_osrm_distances(origin, dests)
        
        for idx, d in zip(cands_idx, real_dists):
            if d is not None:
                df.at[idx, "dist_km"] = d
                
        df = df[df.dist_km <= p.raggio_km].copy()

    summary: dict = {"n": len(df), "q": p.litri_effettivi}
    if df.empty:
        return df, summary

    p_market = float(df.prezzo.median() if p.ref_mode == "mediana" else df.prezzo.mean())
    c_km = p.consumo_l100 / 100 * p_market + p.usura_eur_km
    q = p.litri_effettivi

    if dest is None:
        df["dev_km"] = 2 * df.dist_km
    else:
        dlat, dlon = dest
        d_dest = haversine_km(df.lat.values, df.lon.values, dlat, dlon) * p.road_factor
        d_dir = float(haversine_km(olat, olon, dlat, dlon)) * p.road_factor
        df["dev_km"] = np.clip(df.dist_km + d_dest - d_dir, 0, None)

    df["guadagno"] = q * (p_market - df.prezzo)
    df["brent"] = q * p.alpha * p_market * p.delta_brent
    df["costo_log"] = df.dev_km * c_km
    df["score"] = df.guadagno + df.brent - df.costo_log
    df["peso"] = -df.score
    df["peso_pos"] = df.score.max() - df.score

    pmin, pmax = df.prezzo.min(), df.prezzo.max()
    df["ep"] = 1.0 if pmax == pmin else 1 - (df.prezzo - pmin) / (pmax - pmin)
    n = len(df)
    df["ep_pct"] = 1.0 if n == 1 else 1 - (df.prezzo.rank(method="average") - 1) / (n - 1)

    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", np.arange(1, n + 1))

    best = df.iloc[0]
    sicurezza = p.livello < p.livello_min
    if sicurezza:
        consiglio, motivo = True, f"carburante nel serbatoio sotto la soglia di riserva ({p.livello:.0%} < {p.livello_min:.0%})"
    elif best.score > p.theta:
        consiglio, motivo = True, f"il risparmio migliore ({best.score:+.2f} €) supera la soglia di convenienza ({p.theta:.2f} €)"
    else:
        consiglio, motivo = False, f"il risparmio migliore ({best.score:+.2f} €) non supera la soglia di convenienza ({p.theta:.2f} €)"
    summary.update(
        p_market=p_market, c_km=c_km, best=best, consiglio=consiglio, motivo=motivo,
        p_min=float(pmin), p_max=float(pmax),
    )
    if getattr(p, "use_osrm", True):
        summary["best_route"] = get_osrm_route(origin, (best.lat, best.lon))
    else:
        summary["best_route"] = []

    return df, summary
