"""Storico dei prezzi: mediane giornaliere per comune, carburante e self/servito.

Ogni giorno lo script `scripts/raccogli_storico.py` (lanciato da GitHub Actions) aggiunge al file
`storico/medie_comuni.csv.gz` del branch `dati` una riga per comune, carburante e modalità con la
mediana dei prezzi e il numero di distributori, e aggiorna `storico/comuni.csv.gz` con il centro di
ogni comune (per scegliere i comuni nel raggio). Lo storico può essere riempito a ritroso dagli archivi
trimestrali MIMIT (`medie_da_archivio`).
"""
from __future__ import annotations

import io
import re
import tarfile
from pathlib import Path

import pandas as pd

import fuel_model as fm

COLONNE = ["data", "comune", "provincia", "carburante", "self", "mediana", "n"]
COLONNE_COMUNI = ["comune", "provincia", "lat", "lon"]
GIORNI_TENUTI = 40  # il file tiene solo gli ultimi N giorni (lo score ne usa 30)


def vuoto() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype=t) for c, t in zip(
        COLONNE, ["datetime64[ns]", str, str, str, bool, float, int])})


def centri_comuni(anag: pd.DataFrame) -> pd.DataFrame:
    """Centro di ogni comune: mediana delle coordinate dei suoi distributori."""
    g = anag.groupby(["comune", "provincia"], as_index=False).agg(lat=("lat", "median"), lon=("lon", "median"))
    g[["lat", "lon"]] = g[["lat", "lon"]].round(5)
    return g[COLONNE_COMUNI]


def unisci_comuni(vecchi: pd.DataFrame, nuovi: pd.DataFrame) -> pd.DataFrame:
    """Tiene anche i comuni non più presenti oggi; per gli altri vale il centro più recente."""
    out = pd.concat([vecchi, nuovi], ignore_index=True).drop_duplicates(["comune", "provincia"], keep="last")
    return out.sort_values(["provincia", "comune"]).reset_index(drop=True)[COLONNE_COMUNI]


def medie_giornaliere(anag: pd.DataFrame, prezzi: pd.DataFrame, extraction: pd.Timestamp | None,
                      max_age_days: float = 7) -> pd.DataFrame:
    """Mediana dei prezzi del giorno per comune, carburante e self/servito (stessi filtri dell'app)."""
    if extraction is None:
        raise ValueError("Data di estrazione mancante: non so a che giorno attribuire i prezzi")
    parti = []
    for fuel in fm.FUELS:
        for self_service in (True, False):
            c = fm.build_candidates(anag, prezzi, fuel, self_service, max_age_days, extraction)
            if c.empty:
                continue
            g = c.groupby(["comune", "provincia"], as_index=False).agg(
                mediana=("prezzo", "median"), n=("prezzo", "size"))
            g["carburante"], g["self"] = fuel, self_service
            parti.append(g)
    if not parti:
        return vuoto()
    out = pd.concat(parti, ignore_index=True)
    out["data"] = pd.Timestamp(extraction).normalize()
    out["mediana"] = out.mediana.round(3)
    return out[COLONNE]


def aggiorna(storico: pd.DataFrame, nuove: pd.DataFrame, giorni: int = GIORNI_TENUTI) -> pd.DataFrame:
    """Aggiunge i giorni nuovi (sostituendo quelli già presenti) e tiene solo gli ultimi `giorni`."""
    if nuove.empty:
        return storico
    tieni = storico[~storico.data.isin(nuove.data.unique())]
    out = pd.concat([tieni, nuove], ignore_index=True) if not tieni.empty else nuove.copy()
    limite = out.data.max() - pd.Timedelta(days=giorni - 1)
    out = out[out.data >= limite]
    return out.sort_values(["data", "carburante", "self", "provincia", "comune"]).reset_index(drop=True)[COLONNE]


def _apri(src):
    """bytes → buffer; percorso locale inesistente → None; percorso o URL → invariato."""
    if isinstance(src, (bytes, bytearray)):
        return io.BytesIO(src)
    if isinstance(src, (str, Path)) and not str(src).startswith(("http://", "https://")) and not Path(src).exists():
        return None
    return src


def leggi(src) -> pd.DataFrame:
    """Legge lo storico da un percorso, un URL o dei bytes (CSV compresso con gzip)."""
    src = _apri(src)
    if src is None:
        return vuoto()
    df = pd.read_csv(src, compression="gzip", dtype={"comune": str, "provincia": str, "carburante": str})
    df["data"] = pd.to_datetime(df.data)
    df["self"] = df["self"].astype(str).str.lower().isin(["true", "1"])
    return df[COLONNE]


def leggi_comuni(src) -> pd.DataFrame:
    src = _apri(src)
    if src is None:
        return pd.DataFrame(columns=COLONNE_COMUNI)
    return pd.read_csv(src, compression="gzip", dtype={"comune": str, "provincia": str})[COLONNE_COMUNI]


def scrivi(df: pd.DataFrame, path) -> None:
    """Scrive un CSV gzip deterministico (stesso contenuto → stessi byte, niente commit inutili)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    if "data" in out and pd.api.types.is_datetime64_any_dtype(out["data"]):
        out["data"] = out.data.dt.strftime("%Y-%m-%d")
    out.to_csv(path, index=False, compression={"method": "gzip", "mtime": 0})


# --------------------------------------------------------------------------
# Archivi trimestrali MIMIT (tar.gz con i CSV giornalieri)
# --------------------------------------------------------------------------
def _tipo_e_data(testo: str, nome: str) -> tuple[str | None, pd.Timestamp | None]:
    righe = testo.splitlines()[:2]
    intest = righe[1] if len(righe) > 1 else ""
    if "descCarburante" in intest:
        tipo = "prezzi"
    elif "Latitudine" in intest or "Nome Impianto" in intest:
        tipo = "anagrafica"
    else:
        return None, None
    data = fm._extraction_date(righe[0]) if righe else None
    if data is None:  # ripiego: una data AAAAMMGG o AAAA-MM-GG nel nome del file
        m = re.search(r"(\d{4})-?(\d{2})-?(\d{2})", nome)
        data = pd.Timestamp(f"{m.group(1)}-{m.group(2)}-{m.group(3)}") if m else None
    return tipo, data


def medie_da_archivio(percorsi, dal: pd.Timestamp | None = None, max_age_days: float = 7,
                      log=print) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Mediane giornaliere da uno o più archivi tar.gz MIMIT, solo per i giorni dal `dal` in poi.

    Riconosce i file di prezzi e di anagrafica dall'intestazione e li abbina per data; se manca
    l'anagrafica di un giorno usa la più recente precedente (gli impianti cambiano poco). I CSV
    vengono estratti su disco uno alla volta, perché un trimestre occupa diversi GB.
    Restituisce (mediane giornaliere, centri dei comuni).
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        prezzi_per_giorno: dict[pd.Timestamp, Path] = {}
        anag_per_giorno: dict[pd.Timestamp, Path] = {}
        for percorso in percorsi:
            with tarfile.open(percorso, "r:*") as tar:
                for i, m in enumerate(tar):
                    if not m.isfile() or not m.name.lower().endswith(".csv"):
                        continue
                    f = tar.extractfile(m)
                    if f is None:
                        continue
                    testa = f.read(4000)
                    tipo, data = _tipo_e_data(testa.decode("utf-8-sig", errors="replace"), m.name)
                    if tipo is None or data is None:
                        log(f"  salto {m.name}: tipo o data non riconosciuti")
                        continue
                    data = data.normalize()
                    if tipo == "prezzi" and dal is not None and data < dal:
                        continue
                    dest = Path(tmp) / f"{tipo}_{i}.csv"
                    with open(dest, "wb") as out:
                        out.write(testa)
                        while blocco := f.read(1 << 20):
                            out.write(blocco)
                    (prezzi_per_giorno if tipo == "prezzi" else anag_per_giorno)[data] = dest
        log(f"  trovati {len(prezzi_per_giorno)} giorni di prezzi e {len(anag_per_giorno)} di anagrafica")
        date_anag = sorted(anag_per_giorno)
        parti, comuni = [], pd.DataFrame(columns=COLONNE_COMUNI)
        anag_cache: dict[Path, tuple[pd.DataFrame, pd.DataFrame]] = {}
        for giorno in sorted(prezzi_per_giorno):
            precedenti = [d for d in date_anag if d <= giorno] or date_anag[:1]
            if not precedenti:
                log(f"  salto {giorno:%Y-%m-%d}: nessuna anagrafica disponibile")
                continue
            anag_path = anag_per_giorno[precedenti[-1]]
            if anag_path not in anag_cache:
                anag_parsed, _ = fm.parse_anagrafica(anag_path)
                anag_cache[anag_path] = (anag_parsed, centri_comuni(anag_parsed))
            anag, centri = anag_cache[anag_path]
            prezzi = fm.parse_prezzi(prezzi_per_giorno[giorno])
            parti.append(medie_giornaliere(anag, prezzi, giorno, max_age_days))
            comuni = unisci_comuni(comuni, centri)
            log(f"  {giorno:%Y-%m-%d}: {len(parti[-1])} righe")
    return (pd.concat(parti, ignore_index=True) if parti else vuoto()), comuni
