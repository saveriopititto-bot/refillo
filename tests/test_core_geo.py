import pytest

from core.geo import haversine_km


def test_haversine_stesso_punto():
    assert haversine_km(43.0, 12.0, 43.0, 12.0) == pytest.approx(0.0)


def test_haversine_distanza_nota():
    # Roma (41.9028, 12.4964) -> Milano (45.4642, 9.1900) ~ 477 km
    d = haversine_km(41.9028, 12.4964, 45.4642, 9.1900)
    assert d == pytest.approx(477.0, abs=5.0)
