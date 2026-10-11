"""Download dei file open data MIMIT."""
from __future__ import annotations

# Open data MIMIT, aggiornati ogni giorno (prezzi comunicati entro le 8).
MIMIT_URL = "https://www.mimit.gov.it/images/exportCSV/{name}"
ANAG_FILE = "anagrafica_impianti_attivi.csv"
PREZZI_FILE = "prezzo_alle_8.csv"


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
