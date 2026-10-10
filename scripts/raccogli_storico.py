"""Aggiorna lo storico delle mediane per comune (lanciato ogni giorno da GitHub Actions).

    python scripts/raccogli_storico.py --cartella dati-wt/storico
    python scripts/raccogli_storico.py --cartella ... --archivio URL_O_FILE.tar.gz [--archivio ...]

Senza --archivio scarica i CSV del giorno dal MIMIT; con --archivio legge gli archivi trimestrali
(solo gli ultimi giorni che il file conserva).
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fuel_model as fm  # noqa: E402
import storico  # noqa: E402


def scarica(url: str, dest: Path) -> Path:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (score-rifornimento)"})
    with urlopen(req, timeout=300) as r, open(dest, "wb") as out:
        shutil.copyfileobj(r, out, 1 << 20)
    return dest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cartella", required=True, help="cartella con medie_comuni.csv.gz e comuni.csv.gz")
    ap.add_argument("--archivio", action="append", default=[], help="archivio tar.gz MIMIT (URL o percorso)")
    ap.add_argument("--giorni", type=int, default=storico.GIORNI_TENUTI, help="giorni da conservare")
    a = ap.parse_args(argv)

    f_medie, f_comuni = Path(a.cartella) / "medie_comuni.csv.gz", Path(a.cartella) / "comuni.csv.gz"
    prima = storico.leggi(f_medie)
    print(f"Storico attuale: {len(prima)} righe, {prima.data.nunique()} giorni")
    if a.archivio:
        with tempfile.TemporaryDirectory() as tmp:
            percorsi = []
            for i, src in enumerate(a.archivio):
                if src.startswith(("http://", "https://")):
                    print(f"Scarico {src}")
                    percorsi.append(scarica(src, Path(tmp) / f"archivio_{i}.tar.gz"))
                else:
                    percorsi.append(Path(src))
            dal = pd.Timestamp.today().normalize() - pd.Timedelta(days=a.giorni - 1)
            nuove, comuni = storico.medie_da_archivio(percorsi, dal=dal)
    else:
        anag, extraction = fm.parse_anagrafica(fm.download_csv(fm.ANAG_FILE))
        prezzi = fm.parse_prezzi(fm.download_csv(fm.PREZZI_FILE))
        print(f"Estrazione MIMIT del {extraction:%Y-%m-%d}: {len(anag)} impianti, {len(prezzi)} prezzi")
        nuove = storico.medie_giornaliere(anag, prezzi, extraction)
        comuni = storico.centri_comuni(anag)

    if nuove.empty:
        print("Nessun dato nuovo.")
        return 1
    dopo = storico.aggiorna(prima, nuove, a.giorni)
    storico.scrivi(dopo, f_medie)
    storico.scrivi(storico.unisci_comuni(storico.leggi_comuni(f_comuni), comuni), f_comuni)
    giorni = sorted(nuove.data.dt.strftime("%Y-%m-%d").unique())
    print(f"Aggiunti {len(nuove)} righe per {len(giorni)} giorni ({giorni[0]} … {giorni[-1]}); "
          f"ora {len(dopo)} righe, {dopo.data.nunique()} giorni")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
