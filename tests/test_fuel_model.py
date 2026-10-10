import pandas as pd
import pytest

import fuel_model as fm

ANAG = """Estrazione del 2026-10-09
idImpianto|Gestore|Bandiera|Tipo Impianto|Nome Impianto|Indirizzo|Comune|Provincia|Latitudine|Longitudine
1|G1|Agip Eni|Stradale|Eni Uno|Via Roma 1|Gualdo Tadino|PG|43.2300|12.7800
2|G2|Q8|Stradale|Q8 | Due|Via Flaminia 2|Gualdo Tadino|PG|43.2400|12.7900
3|G3|IP|Stradale|IP Tre|Via Lontana 3|Roma|RM|41.9000|12.5000
4|G4|IP|Stradale|Fuori|Via X|Estero|XX|60.0|30.0
"""

PREZZI = """Estrazione del 2026-10-09
idImpianto|descCarburante|prezzo|isSelf|dtComu
1|Benzina|1.800|1|09/10/2026 07:00:00
2|Benzina|1.700|1|09/10/2026 07:00:00
2|Benzina|1.750|1|01/10/2026 07:00:00
3|Benzina|1.600|1|09/10/2026 07:00:00
1|Gasolio|1.700|1|01/01/2026 07:00:00
"""


@pytest.fixture
def dati():
    anag, extraction = fm.parse_anagrafica(ANAG.encode())
    return anag, fm.parse_prezzi(PREZZI.encode()), extraction


def test_parse_anagrafica(dati):
    anag, _, extraction = dati
    assert extraction == pd.Timestamp("2026-10-09")
    assert list(anag.id) == ["1", "2", "3"]  # il 4 è fuori dall'Italia
    riga = anag[anag.id == "2"].iloc[0]  # '|' in più nel nome
    assert riga.comune == "GUALDO TADINO" and riga.lat == pytest.approx(43.24)


def test_parse_anagrafica_senza_data():
    anag, extraction = fm.parse_anagrafica(ANAG.replace("2026-10-09", "ieri").encode())
    assert extraction is None and len(anag) == 3


def test_build_candidates_filtra_eta_e_duplicati(dati):
    anag, prezzi, extraction = dati
    c = fm.build_candidates(anag, prezzi, "Benzina", True, 7, extraction)
    assert c.set_index("id").prezzo.to_dict() == {"1": 1.8, "2": 1.7, "3": 1.6}
    assert fm.build_candidates(anag, prezzi, "Gasolio", True, 7, extraction).empty


def test_brent_delta_limitato():
    assert fm.brent_delta(120, 100) == pytest.approx(0.10)
    assert fm.brent_delta(105, 100) == pytest.approx(0.05)
    assert fm.brent_delta(100, 100, 1.0, 1.1) == pytest.approx(0.10)


def test_compute_edges(dati):
    anag, prezzi, extraction = dati
    c = fm.build_candidates(anag, prezzi, "Benzina", True, 7, extraction)
    p = fm.ModelParams(v_tot=50, livello=0.2, raggio_km=10)
    edges, info = fm.compute_edges(c, (43.23, 12.78), p)
    assert info["n"] == 2  # Roma è fuori raggio
    assert info["q"] == pytest.approx(40)
    assert edges.iloc[0].id == "2"  # più economico, poco più lontano
    assert (edges.score == edges.guadagno + edges.brent - edges.costo_log).all()
    assert (edges.peso_pos >= 0).all()
    assert info["decisione"] == (edges.score.max() > p.theta)


def test_compute_edges_vuoto(dati):
    anag, prezzi, extraction = dati
    c = fm.build_candidates(anag, prezzi, "Benzina", True, 7, extraction)
    edges, info = fm.compute_edges(c, (45.0, 9.0), fm.ModelParams(raggio_km=5))
    assert edges.empty and info["n"] == 0
