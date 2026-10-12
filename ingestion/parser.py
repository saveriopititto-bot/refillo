"""Parsing e costruzione dei candidati dai CSV MIMIT."""
from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd

from core.geo import ITALY_BBOX, haversine_km

# Solo i prodotti "standard": le varianti premium (Blue Diesel, V-Power, ...)
# hanno prezzi diversi e falserebbero il confronto.
FUELS = ("Benzina", "Gasolio", "GPL", "Metano")

# GPL e Metano si vendono quasi sempre solo serviti: per loro la scelta Self/Servito non vale e si usa il prezzo
# che c'è (se un distributore ha entrambi, il più basso).
SENZA_SELF = ("GPL", "Metano")
# Unità di misura del prezzo (€ per unità); il Metano si vende a kg, gli altri a litri.
UNITA = {"Metano": "kg"}


def unita(fuel: str) -> str:
    """«kg» per il Metano, «l» per gli altri carburanti."""
    return UNITA.get(fuel, "l")


# Intervalli plausibili (€/l, Metano €/kg) per scartare errori di inserimento.
PRICE_BOUNDS = {
    "Benzina": (0.8, 3.5),
    "Gasolio": (0.8, 3.5),
    "GPL": (0.3, 2.0),
    "Metano": (0.8, 3.5),
}


def _to_bytes(src) -> bytes:
    if isinstance(src, (str, Path)):
        return Path(src).read_bytes()
    if isinstance(src, (bytes, bytearray)):
        return bytes(src)
    data = src.read()
    return data.encode("utf-8") if isinstance(data, str) else data


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


# Coordinate sbagliate nell'anagrafica MIMIT: alcuni distributori hanno le coordinate di un'altra città (spesso il centro
# di Milano, Roma o Palermo) e comparirebbero come «il migliore, a pochi metri» a chi sta lì.
SOGLIA_COMUNE_KM = 50  # oltre questa distanza dal centro dei distributori del suo comune (Roma arriva a ~26 km, le Eolie a ~42)
SOGLIA_PROVINCIA_KM = 200  # comuni con un solo distributore: distanza dal centro della provincia (larga per le isole)


def coordinate_sospette(anag: pd.DataFrame) -> pd.Series:
    """True per i distributori con coordinate in conflitto con il loro comune.

    Centro del comune = mediana delle coordinate dei suoi distributori (con 3 o più regge a un errore). Con 2 soli
    distributori a più di SOGLIA_COMUNE_KM l'uno dall'altro non si sa quale sia giusto: sono sospetti tutti e due.
    Con 1 solo si guarda la provincia."""
    if anag.empty:
        return pd.Series(False, index=anag.index)
    chiave = ["comune", "provincia"]
    n = anag.groupby(chiave)["lat"].transform("size")
    centro = anag.groupby(chiave)[["lat", "lon"]].transform("median")
    d_comune = haversine_km(anag.lat.values, anag.lon.values, centro.lat.values, centro.lon.values)
    prov = anag.groupby("provincia")[["lat", "lon"]].transform("median")
    d_prov = haversine_km(anag.lat.values, anag.lon.values, prov.lat.values, prov.lon.values)
    # con 2 distributori il centro è a metà strada: lontani più della soglia = ognuno a più di metà soglia dal centro
    return pd.Series(((n >= 3) & (d_comune > SOGLIA_COMUNE_KM))
                     | ((n == 2) & (d_comune > SOGLIA_COMUNE_KM / 2))
                     | ((n == 1) & (d_prov > SOGLIA_PROVINCIA_KM)), index=anag.index)


def parse_prezzi(src) -> pd.DataFrame:
    """Legge prezzo_alle_8.csv (separatore '|', 1ª riga = titolo)."""
    # dai byte, senza passare da una stringa Python: lettura circa due volte più veloce
    df = pd.read_csv(io.BytesIO(_to_bytes(src)), sep="|", skiprows=1, dtype=str, on_bad_lines="skip",
                     encoding="utf-8-sig", encoding_errors="replace")
    df = df.rename(
        columns={"idImpianto": "id", "descCarburante": "carburante", "isSelf": "is_self", "dtComu": "dt_comu"}
    )
    df["id"] = df["id"].str.strip()
    df["carburante"] = df["carburante"].str.strip().astype("category")  # pochi valori ripetuti: meno memoria
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
    """Un record per distributore: anagrafica + prezzo del carburante scelto.

    Per GPL e Metano (SENZA_SELF) self_service non conta: si tengono self e servito e, se un distributore li ha
    entrambi, il prezzo più basso."""
    p = prezzi[prezzi.carburante.str.lower() == fuel.lower()]
    if fuel not in SENZA_SELF:
        p = p[p.is_self == self_service]
    lo, hi = PRICE_BOUNDS.get(fuel, (0.0, 10.0))
    p = p[p.prezzo.between(lo, hi)]
    if max_age_days is not None and extraction_date is not None:
        limite = extraction_date + pd.Timedelta(days=1) - pd.Timedelta(days=max_age_days)
        p = p[p.dt_comu >= limite]
    p = p.sort_values("dt_comu").drop_duplicates(["id", "is_self"], keep="last")  # l'ultimo prezzo comunicato
    p = p.sort_values("prezzo", kind="stable").drop_duplicates("id")  # tra self e servito (GPL, Metano) il più basso
    out = anag.merge(p[["id", "prezzo", "dt_comu"]], on="id", how="inner")
    if extraction_date is not None:
        out["eta_giorni"] = (extraction_date + pd.Timedelta(days=1) - out["dt_comu"]).dt.total_seconds() / 86400
    return out.reset_index(drop=True)
