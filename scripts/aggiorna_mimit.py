"""Scarica i CSV giornalieri dal sito MIMIT e li salva nella cartella data/.

Utilizzato da GitHub Actions ogni mattina per mantenere i file pronti e aggiornati
sul repository, così l'app Streamlit li legge direttamente in locale.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fuel_model as fm  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dest",
        default="data",
        help="Cartella di destinazione per i CSV (default: data/)",
    )
    args = parser.parse_args(argv)

    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"Download anagrafica ({fm.ANAG_FILE}) dal MIMIT...")
    anag_b = fm.download_csv(fm.ANAG_FILE)
    anag_df, extraction = fm.parse_anagrafica(anag_b)
    if anag_df.empty:
        print("Errore: l'anagrafica scaricata è vuota!", file=sys.stderr)
        return 1
    print(f"Anagrafica valida: {len(anag_df)} impianti trovati (estrazione: {extraction}).")

    print(f"Download prezzi alle 8 ({fm.PREZZI_FILE}) dal MIMIT...")
    prezzi_b = fm.download_csv(fm.PREZZI_FILE)
    prezzi_df = fm.parse_prezzi(prezzi_b)
    if prezzi_df.empty:
        print("Errore: il file dei prezzi scaricato è vuoto!", file=sys.stderr)
        return 1
    print(f"Prezzi validi: {len(prezzi_df)} rilevazioni di prezzo trovate.")

    f_anag = dest_dir / fm.ANAG_FILE
    f_prezzi = dest_dir / fm.PREZZI_FILE

    f_anag.write_bytes(anag_b)
    f_prezzi.write_bytes(prezzi_b)

    mb_a = len(anag_b) / (1024 * 1024)
    mb_p = len(prezzi_b) / (1024 * 1024)
    print(f"Salvati con successo in {dest_dir}:")
    print(f" - {f_anag.name}: {mb_a:.2f} MB")
    print(f" - {f_prezzi.name}: {mb_p:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
