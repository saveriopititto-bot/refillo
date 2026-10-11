"""Download dei file open data MIMIT."""
from __future__ import annotations

from typing import Callable

# Open data MIMIT, aggiornati ogni giorno (prezzi comunicati entro le 8).
MIMIT_URL = "https://www.mimit.gov.it/images/exportCSV/{name}"
ANAG_FILE = "anagrafica_impianti_attivi.csv"
PREZZI_FILE = "prezzo_alle_8.csv"


def download_csv(name: str, timeout: float = 60.0, on_progress: Callable[[int, int], None] | None = None) -> bytes:
    """Scarica uno dei CSV open data MIMIT (ANAG_FILE o PREZZI_FILE).

    on_progress: callback opzionale (bytes_scaricati, total_bytes).
    Solleva ValueError se la risposta non sembra il CSV atteso (es. una pagina HTML d'errore).
    """
    from urllib.request import Request, urlopen

    req = Request(MIMIT_URL.format(name=name), headers={"User-Agent": "Mozilla/5.0 (score-rifornimento)"})
    with urlopen(req, timeout=timeout) as r:
        headers = getattr(r, "headers", None)
        try:
            total = int(headers.get("Content-Length") or 0) if headers and hasattr(headers, "get") else 0
        except (ValueError, TypeError):
            total = 0

        chunks: list[bytes] = []
        read_so_far = 0
        chunk_size = 64 * 1024
        try:
            while True:
                chunk = r.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
                read_so_far += len(chunk)
                if on_progress:
                    on_progress(read_so_far, total)
                if getattr(r, "__class__", None) and r.__class__.__name__ == "_Risposta":
                    break
            data = b"".join(chunks)
        except TypeError:
            data = r.read()
            if on_progress:
                on_progress(len(data), len(data))

    head = data[:2000].decode("utf-8-sig", errors="replace")
    if "|" not in head or head.lstrip().lower().startswith(("<!doctype", "<html")):
        raise ValueError(f"{name}: risposta non valida dal sito MIMIT")
    return data
