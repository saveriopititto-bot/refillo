"""Scarica i CSV giornalieri dal sito MIMIT e li salva compressi (.csv.gz) in una cartella.

Lanciato ogni mattina da .github/workflows/aggiorna_mimit.yml, che salva i file nel branch `dati`
(cartella mimit/): l'app li scarica da lì, più veloce del sito del ministero.
"""
from __future__ import annotations

import argparse
import gzip
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fuel_model as fm  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dest",
        default="mimit",
        help="Cartella di destinazione per i CSV compressi (default: mimit/)",
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

    f_anag = dest_dir / f"{fm.ANAG_FILE}.gz"
    f_prezzi = dest_dir / f"{fm.PREZZI_FILE}.gz"

    # mtime=0: stessi dati, stesso file, così git non vede modifiche se il MIMIT non ha aggiornato nulla
    f_anag.write_bytes(gzip.compress(anag_b, mtime=0))
    f_prezzi.write_bytes(gzip.compress(prezzi_b, mtime=0))

    mb_a = f_anag.stat().st_size / (1024 * 1024)
    mb_p = f_prezzi.stat().st_size / (1024 * 1024)
    print(f"Salvati con successo in {dest_dir}:")
    print(f" - {f_anag.name}: {mb_a:.2f} MB")
    print(f" - {f_prezzi.name}: {mb_p:.2f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
