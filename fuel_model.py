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
import requests
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

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
# Modello
# --------------------------------------------------------------------------
@dataclass
class ModelParams:
    v_tot: float = 50.0            # capacità serbatoio (l)
    livello: float = 0.25          # L in [0, 1]
    litri: float | None = None     # q; None -> v_tot * (1 - L)
    alpha: float = 0.2             # pass-through del Brent, [0, 0.4]
    delta_brent: float = 0.0       # dB relativo (già limitato)
    consumo_l100: float = 5.0      # l/100 km
    usura_eur_km: float = 0.05     # costo variabile di usura (€/km)
    road_factor: float = 1.3       # km su strada / km in linea d'aria
    raggio_km: float = 20.0        # raggio d'azione (km su strada stimati)
    use_osrm: bool = True          # usa OSRM per i percorsi reali
    ref_mode: str = "mediana"      # "mediana" | "media" per P_market
    theta: float = 0.0             # soglia di consiglio (€)
    livello_min: float = 0.10      # L_min: sotto questa soglia si rifornisce comunque

    @property
    def litri_effettivi(self) -> float:
        cap = self.v_tot * (1 - self.livello)
        return cap if self.litri is None else float(min(self.litri, cap))


def get_osrm_distances(origin: tuple[float, float], destinations: list[tuple[float, float]]) -> list[float | None]:
    """Ottiene le distanze stradali in km usando l'API pubblica di OSRM (max 99 destinazioni)."""
    if not destinations:
        return []
    
    # OSRM si aspetta lon,lat
    coords = [f"{origin[1]:.5f},{origin[0]:.5f}"]
    for lat, lon in destinations:
        coords.append(f"{lon:.5f},{lat:.5f}")
    
    url = f"http://router.project-osrm.org/table/v1/driving/{';'.join(coords)}?sources=0"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == "Ok" and "distances" in data and data["distances"]:
                # La prima riga contiene le distanze dall'origine a tutti i punti
                return [d / 1000.0 if d is not None else None for d in data["distances"][0][1:]]
    except Exception as e:
        print(f"Errore OSRM: {e}")
        pass
    
    return [None] * len(destinations)


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
    return df, summary
