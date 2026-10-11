"""Calcoli geometrici e costanti geografiche."""
from __future__ import annotations

import numpy as np

EARTH_RADIUS_KM = 6371.0088

# Bounding box approssimativa per l'Italia (lat_min, lat_max, lon_min, lon_max)
ITALY_BBOX = (35.0, 48.0, 6.0, 19.0)


def haversine_km(lat1, lon1, lat2, lon2):
    """Calcola la distanza geodetica ortodromica in km tra due punti via formula Haversine."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))
