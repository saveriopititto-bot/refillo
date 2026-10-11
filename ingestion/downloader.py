"""Download dei file open data MIMIT (dal sito del ministero o dalla copia nel branch `dati`)."""
from __future__ import annotations

import gzip
from typing import Callable

# Open data MIMIT, aggiornati ogni giorno (prezzi comunicati entro le 8).
MIMIT_URL = "https://www.mimit.gov.it/images/exportCSV/{name}"
ANAG_FILE = "anagrafica_impianti_attivi.csv"
PREZZI_FILE = "prezzo_alle_8.csv"
# Copia compressa salvata ogni mattina da .github/workflows/aggiorna_mimit.yml nel branch `dati`.
DATI_URL = "https://raw.githubusercontent.com/saveriopititto-bot/refillo/dati/mimit/{name}.gz"


def _scarica(url: str, timeout: float, on_progress: Callable[[int, int], None] | None) -> bytes:
    from urllib.request import Request, urlopen

    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (score-rifornimento)"})
    with urlopen(req, timeout=timeout) as r:
        try:
            total = int(r.headers.get("Content-Length") or 0)
        except (AttributeError, ValueError, TypeError):
            total = 0
        chunks: list[bytes] = []
        letti = 0
        while chunk := r.read(64 * 1024):
            chunks.append(chunk)
            letti += len(chunk)
            if on_progress:
                on_progress(letti, total)
    return b"".join(chunks)


def _controlla(name: str, data: bytes, fonte: str) -> bytes:
    """Solleva ValueError se i dati non sembrano il CSV atteso (es. una pagina HTML d'errore)."""
    head = data[:2000].decode("utf-8-sig", errors="replace")
    if "|" not in head or head.lstrip().lower().startswith(("<!doctype", "<html")):
        raise ValueError(f"{name}: risposta non valida da {fonte}")
    return data


def download_csv(name: str, timeout: float = 60.0, on_progress: Callable[[int, int], None] | None = None) -> bytes:
    """Scarica uno dei CSV open data MIMIT (ANAG_FILE o PREZZI_FILE) dal sito del ministero.

    on_progress: callback opzionale (bytes_scaricati, total_bytes).
    Solleva ValueError se la risposta non sembra il CSV atteso (es. una pagina HTML d'errore).
    """
    return _controlla(name, _scarica(MIMIT_URL.format(name=name), timeout, on_progress), "sito MIMIT")


def download_dati(name: str, timeout: float = 30.0, on_progress: Callable[[int, int], None] | None = None) -> bytes:
    """Scarica la copia del CSV MIMIT salvata ogni mattina nel branch `dati` (compressa con gzip)."""
    data = gzip.decompress(_scarica(DATI_URL.format(name=name), timeout, on_progress))
    return _controlla(name, data, "branch dati")
