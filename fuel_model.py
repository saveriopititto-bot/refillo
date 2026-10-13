"""Punto d'accesso unico al modello: riesporta da core, ingestion e clients quello che usano l'app, gli script e i test
(importato come `fm`)."""
from __future__ import annotations

import requests  # i test sostituiscono fm.requests.get per simulare OSRM e Supabase

from clients.osrm import _osrm_route, _osrm_table, get_osrm_distances, get_osrm_minuti, get_osrm_route
from clients.supabase import BRENT_SCORE_TESTI, fetch_brent_score
from clients.yahoo import fetch_brent_yf
from core.geo import ITALY_BBOX, haversine_km
from core.model import brent_delta, compute_edges
from core.types import ModelParams
from ingestion.downloader import ANAG_FILE, PREZZI_FILE, download_csv, download_dati
from ingestion.parser import (
    FUELS,
    SENZA_SELF,
    _extraction_date,
    build_candidates,
    coordinate_sospette,
    parse_anagrafica,
    parse_prezzi,
    unita,
)

__all__ = [
    "ANAG_FILE",
    "BRENT_SCORE_TESTI",
    "FUELS",
    "ITALY_BBOX",
    "ModelParams",
    "PREZZI_FILE",
    "SENZA_SELF",
    "_extraction_date",
    "_osrm_route",
    "_osrm_table",
    "brent_delta",
    "build_candidates",
    "compute_edges",
    "coordinate_sospette",
    "download_csv",
    "download_dati",
    "fetch_brent_score",
    "fetch_brent_yf",
    "get_osrm_distances",
    "get_osrm_minuti",
    "get_osrm_route",
    "haversine_km",
    "parse_anagrafica",
    "parse_prezzi",
    "requests",
    "unita",
]
