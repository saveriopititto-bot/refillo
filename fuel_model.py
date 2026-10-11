"""Modello di scoring razionale per il rifornimento (facade di retrocompatibilità).

Questo modulo riesporta tutti i simboli dai moduli specializzati (core, ingestion, clients)
per garantire piena retrocompatibilità con i test, l'interfaccia Streamlit e gli script.
"""
from __future__ import annotations

import requests  # riesportato per retrocompatibilità e test fixture

from clients.osrm import (
    OSRM_URL,
    _arrotonda,
    _osrm_route,
    _osrm_table,
    get_osrm_distances,
    get_osrm_route,
)
from clients.supabase import (
    BRENT_SCORE_TABELLA,
    BRENT_SCORE_TESTI,
    fetch_brent_score,
)
from clients.yahoo import fetch_brent_yf
from core.geo import (
    EARTH_RADIUS_KM,
    ITALY_BBOX,
    haversine_km,
)
from core.model import (
    brent_delta,
    compute_edges,
)
from core.types import (
    SCONTO_MAX,
    BrentScoreResult,
    BrentYfResult,
    ModelParams,
    ModelSummary,
)
from ingestion.downloader import (
    ANAG_FILE,
    DATI_URL,
    MIMIT_URL,
    PREZZI_FILE,
    download_csv,
    download_dati,
)
from ingestion.parser import (
    FUELS,
    PRICE_BOUNDS,
    _extraction_date,
    _to_bytes,
    _to_text,
    build_candidates,
    parse_anagrafica,
    parse_prezzi,
)

__all__ = [
    "ANAG_FILE",
    "BRENT_SCORE_TABELLA",
    "BRENT_SCORE_TESTI",
    "BrentScoreResult",
    "BrentYfResult",
    "DATI_URL",
    "EARTH_RADIUS_KM",
    "FUELS",
    "ITALY_BBOX",
    "MIMIT_URL",
    "ModelParams",
    "ModelSummary",
    "OSRM_URL",
    "PREZZI_FILE",
    "PRICE_BOUNDS",
    "SCONTO_MAX",
    "_arrotonda",
    "_extraction_date",
    "_osrm_route",
    "_osrm_table",
    "_to_bytes",
    "_to_text",
    "brent_delta",
    "build_candidates",
    "compute_edges",
    "download_csv",
    "download_dati",
    "fetch_brent_score",
    "fetch_brent_yf",
    "get_osrm_distances",
    "get_osrm_route",
    "haversine_km",
    "parse_anagrafica",
    "parse_prezzi",
    "requests",
]
