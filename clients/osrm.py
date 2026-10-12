"""Client per l'API pubblica OSRM (Open Source Routing Machine)."""
from __future__ import annotations

import logging
import time
from functools import lru_cache

import requests

logger = logging.getLogger(__name__)

# dopo un errore OSRM non si richiama per qualche minuto (per tutti, è lo stesso server): intanto linea d'aria,
# così se il servizio è giù ogni tocco non aspetta fino a 4 secondi
PAUSA_DOPO_ERRORE_S = 180
_pausa_fino = 0.0


def in_pausa() -> bool:
    return time.monotonic() < _pausa_fino


class InPausa(Exception):
    """OSRM non si chiama: c'è stato un errore da poco. Le risposte già in memoria valgono comunque."""


def _errore(cosa: str, e: Exception) -> None:
    global _pausa_fino
    if isinstance(e, InPausa):
        return
    _pausa_fino = time.monotonic() + PAUSA_DOPO_ERRORE_S
    logger.warning("Errore OSRM %s: %s (pausa di %d s)", cosa, e, PAUSA_DOPO_ERRORE_S)


def riprendi() -> None:
    """Toglie la pausa (per i test)."""
    global _pausa_fino
    _pausa_fino = 0.0

OSRM_URL = "https://router.project-osrm.org"


@lru_cache(maxsize=512)
def _osrm_table(origin: tuple[float, float], destinations: tuple[tuple[float, float], ...]) -> tuple:
    """Distanze stradali (km) dall'origine; solleva un'eccezione se OSRM non risponde, così l'errore non va in cache."""
    if in_pausa():
        raise InPausa()
    coords = ";".join(f"{lon:.5f},{lat:.5f}" for lat, lon in (origin, *destinations))  # OSRM vuole lon,lat
    resp = requests.get(f"{OSRM_URL}/table/v1/driving/{coords}",
                        params={"sources": "0", "annotations": "distance"}, timeout=2.5)
    if resp.status_code != 200:
        raise ValueError(f"OSRM ha risposto {resp.status_code}")
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("distances"):
        raise ValueError(f"OSRM: {data.get('code')}")
    # la prima riga contiene le distanze dall'origine a tutti i punti
    return tuple(d / 1000.0 if d is not None else None for d in data["distances"][0][1:])


@lru_cache(maxsize=256)
def _osrm_route(origin: tuple[float, float], dest: tuple[float, float]) -> tuple:
    if in_pausa():
        raise InPausa()
    coords = f"{origin[1]:.5f},{origin[0]:.5f};{dest[1]:.5f},{dest[0]:.5f}"
    resp = requests.get(f"{OSRM_URL}/route/v1/driving/{coords}",
                        params={"geometries": "geojson", "overview": "full"}, timeout=1.5)
    if resp.status_code != 200:
        raise ValueError(f"OSRM ha risposto {resp.status_code}")
    data = resp.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError(f"OSRM: {data.get('code')}")
    return tuple(tuple(c) for c in data["routes"][0]["geometry"]["coordinates"])


def _arrotonda(punto: tuple[float, float]) -> tuple[float, float]:
    """Arrotonda a 5 decimali (~1 m), gli stessi dell'URL OSRM per riusare la cache."""
    return round(float(punto[0]), 5), round(float(punto[1]), 5)


def get_osrm_distances(origin: tuple[float, float], destinations: list[tuple[float, float]]) -> list[float | None]:
    """Distanze stradali in km dall'API pubblica di OSRM (max 99 destinazioni); None dove non disponibili."""
    if not destinations:
        return []
    try:
        return list(_osrm_table(_arrotonda(origin), tuple(_arrotonda(d) for d in destinations)))
    except Exception as e:
        _errore("table", e)
        return [None] * len(destinations)


def get_osrm_route(origin: tuple[float, float], dest: tuple[float, float]) -> list[list[float]]:
    """Geometria del percorso reale (GeoJSON: lista di [lon, lat]) dal server OSRM; [] se non disponibile."""
    try:
        return [list(c) for c in _osrm_route(_arrotonda(origin), _arrotonda(dest))]
    except Exception as e:
        _errore("route", e)
        return []
