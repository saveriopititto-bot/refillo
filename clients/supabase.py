"""Client per Supabase (tabella brent_score)."""
from __future__ import annotations

import pandas as pd
import requests

from core.types import BrentScoreResult

BRENT_SCORE_TABELLA = "brent_score"
# esito -> etichetta; +1 = il Brent è sopra la media dei 30 giorni più del normale
BRENT_SCORE_TESTI = {1: "Conviene", 0: "Rifornisci", -1: "Aspetta"}


def fetch_brent_score(url: str, chiave: str, timeout: float = 15) -> BrentScoreResult:
    """Ultimo score del Brent dalla tabella brent_score di Supabase, letta con la chiave pubblica (anon).

    Restituisce data (giorno di borsa), esito (+1 Conviene, 0 Rifornisci, -1 Aspetta: BRENT_SCORE_TESTI), score, brent_eur,
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
