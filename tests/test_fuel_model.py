import numpy as np
import pandas as pd
import pytest

import clients.osrm as osrm
import fuel_model as fm


@pytest.fixture(autouse=True)
def _osrm_senza_pausa():
    """Ogni test parte senza la pausa di OSRM lasciata da un errore di un altro test."""
    osrm.riprendi()
    yield
    osrm.riprendi()


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


def test_build_candidates_gpl_metano_ignorano_self(dati):
    anag, _, extraction = dati
    prezzi = fm.parse_prezzi("""Estrazione del 2026-10-09
idImpianto|descCarburante|prezzo|isSelf|dtComu
1|GPL|0.790|0|09/10/2026 07:00:00
1|GPL|0.760|1|09/10/2026 07:00:00
2|GPL|0.800|0|09/10/2026 07:00:00
2|GPL|0.700|0|01/10/2026 07:00:00
3|Metano|1.900|0|09/10/2026 07:00:00
""".encode())
    # GPL: self e servito valgono entrambi; con tutti e due il più basso; per lo stesso tipo l'ultimo comunicato
    for self_service in (True, False):
        c = fm.build_candidates(anag, prezzi, "GPL", self_service, 30, extraction)
        assert c.set_index("id").prezzo.to_dict() == {"1": 0.76, "2": 0.80}
    assert fm.build_candidates(anag, prezzi, "Metano", True, 30, extraction).id.tolist() == ["3"]
    assert fm.unita("Metano") == "kg" and fm.unita("GPL") == "l" and fm.unita("Benzina") == "l"


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
    assert info["consiglio"] == (edges.score.max() > p.theta)


def test_compute_edges_scarta_prezzi_troppo_bassi():
    c = pd.DataFrame({"id": list("abcde"), "lat": [43.23] * 5, "lon": [12.78] * 5,
                      "prezzo": [1.69, 1.70, 1.80, 1.85, 1.90]})
    edges, info = fm.compute_edges(c, (43.23, 12.78), fm.ModelParams(use_osrm=False))
    assert sorted(edges.id) == list("bcde") and info["n"] == 4
    assert info["p_market"] == pytest.approx(1.80)
    edges, info = fm.compute_edges(c, (43.23, 12.78), fm.ModelParams(use_osrm=False, sconto_max=None))
    assert info["n"] == 5


def test_compute_edges_conti_a_mano():
    # tre distributori a 0, 5 e 3 km in linea d'aria (× 1,3 di strada), Brent +5%
    c = pd.DataFrame({"id": ["A", "B", "C"], "lat": [43.0, 43.0 + 5 / 111.195, 43.0],
                      "lon": [12.0, 12.0, 12.0 + 3 / (111.195 * np.cos(np.radians(43)))],
                      "prezzo": [1.80, 1.75, 1.90]})
    p = fm.ModelParams(v_tot=50, livello=0.25, alpha=0.2, delta_brent=0.05, consumo_l100=6,
                       usura_eur_km=0.05, road_factor=1.3, use_osrm=False)
    edges, info = fm.compute_edges(c, (43.0, 12.0), p)
    q, pm = 37.5, 1.80
    c_km = 6 / 100 * pm + 0.05
    assert info["c_km"] == pytest.approx(c_km)
    for r in edges.itertuples():
        d = {"A": 0.0, "B": 5 * 1.3, "C": 3 * 1.3}[r.id]
        assert r.dist_km == pytest.approx(d, abs=0.01)
        assert r.risparmio == pytest.approx(q * (pm - r.prezzo) - 2 * d * c_km, abs=0.01)
        assert r.score == pytest.approx(r.risparmio + q * 0.2 * pm * 0.05)
    assert edges.id.iloc[0] == "A" and edges.risparmio.iloc[0] == pytest.approx(0)  # al prezzo medio, sotto casa
    assert not info["riserva"]


def test_compute_edges_riserva(dati):
    anag, prezzi, extraction = dati
    c = fm.build_candidates(anag, prezzi, "Benzina", True, 7, extraction)
    p = fm.ModelParams(livello=0.05, livello_min=0.10, theta=1000, raggio_km=10, use_osrm=False)
    _, info = fm.compute_edges(c, (43.23, 12.78), p)
    assert info["riserva"] and info["consiglio"]  # sotto riserva si rifornisce anche se non conviene


def test_compute_edges_vuoto(dati):
    anag, prezzi, extraction = dati
    c = fm.build_candidates(anag, prezzi, "Benzina", True, 7, extraction)
    edges, info = fm.compute_edges(c, (45.0, 9.0), fm.ModelParams(raggio_km=5))
    assert edges.empty and info["n"] == 0 and not info["riserva"]


def test_compute_edges_tutti_scartati_da_sconto_max():
    # se sconto_max scarta candidati anomali (es. prezzo < p_market - sconto_max)
    c_two = pd.DataFrame({"id": ["a", "b"], "lat": [43.23, 43.23], "lon": [12.78, 12.78], "prezzo": [1.00, 2.00]})
    edges, _info = fm.compute_edges(c_two, (43.23, 12.78), fm.ModelParams(use_osrm=False, sconto_max=0.10))
    # 'a' ha prezzo 1.00 che dista 0.50 dalla mediana 1.50 -> scartato
    assert len(edges) == 1 and edges.iloc[0].id == "b"


class _Risposta:
    def __init__(self, data: bytes):
        self.data = data
        self.headers = {"Content-Length": str(len(data))}

    def read(self, n=-1):
        letto, self.data = (self.data, b"") if n < 0 else (self.data[:n], self.data[n:])
        return letto

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_download_csv(monkeypatch):
    chiamate = []

    def finto_urlopen(req, timeout):
        chiamate.append(req.full_url)
        return _Risposta(ANAG.encode())

    monkeypatch.setattr("urllib.request.urlopen", finto_urlopen)
    data = fm.download_csv(fm.ANAG_FILE)
    assert chiamate == ["https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"]
    assert len(fm.parse_anagrafica(data)[0]) == 3


def test_download_dati_decomprime(monkeypatch):
    import gzip

    chiamate, progressi = [], []

    def finto_urlopen(req, timeout):
        chiamate.append(req.full_url)
        return _Risposta(gzip.compress(PREZZI.encode()))

    monkeypatch.setattr("urllib.request.urlopen", finto_urlopen)
    data = fm.download_dati(fm.PREZZI_FILE, on_progress=lambda letti, totale: progressi.append((letti, totale)))
    assert chiamate == ["https://raw.githubusercontent.com/saveriopititto-bot/refillo/dati/mimit/prezzo_alle_8.csv.gz"]
    assert data == PREZZI.encode()
    assert progressi and progressi[-1][0] == progressi[-1][1]


def test_download_csv_rifiuta_html(monkeypatch):
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda req, timeout: _Risposta(b"<!DOCTYPE html><html>errore | manutenzione</html>"))
    with pytest.raises(ValueError):
        fm.download_csv(fm.PREZZI_FILE)


# --------------------------------------------------------------------------
# Score del Brent da Supabase
# --------------------------------------------------------------------------
class _RispostaJSON:
    def __init__(self, stato, corpo):
        self.status_code, self._corpo = stato, corpo

    def json(self):
        return self._corpo


RIGA_SCORE = {"data": "2026-10-09", "esito": 1, "score": 1.42, "brent_eur": 70.5, "media_30_eur": 66.0,
              "aggiornato_il": "2026-10-09T22:31:00+00:00"}


def test_fetch_brent_score(monkeypatch):
    chiamate = []

    def finto_get(url, params=None, headers=None, timeout=None):
        chiamate.append((url, params, headers))
        return _RispostaJSON(200, [RIGA_SCORE])

    monkeypatch.setattr(fm.requests, "get", finto_get)
    s = fm.fetch_brent_score("https://prova.supabase.co/", "chiave-anon")
    url, params, headers = chiamate[0]
    assert url == "https://prova.supabase.co/rest/v1/brent_score"
    assert params["order"] == "data.desc" and params["limit"] == "1"
    assert headers["apikey"] == "chiave-anon"
    assert s["esito"] == 1 and s["data"] == pd.Timestamp("2026-10-09")
    assert s["brent_eur"] == pytest.approx(70.5) and s["media_30_eur"] == pytest.approx(66.0)
    assert set(fm.BRENT_SCORE_TESTI) == {1, 0, -1}


@pytest.mark.parametrize("risposta, messaggio", [
    (_RispostaJSON(200, []), "vuota"),
    (_RispostaJSON(401, {"message": "Invalid API key"}), "401"),
    (_RispostaJSON(200, [dict(RIGA_SCORE, esito=2)]), "esito non valido"),
])
def test_fetch_brent_score_errori(monkeypatch, risposta, messaggio):
    monkeypatch.setattr(fm.requests, "get", lambda *a, **k: risposta)
    with pytest.raises(ValueError, match=messaggio):
        fm.fetch_brent_score("https://prova.supabase.co", "chiave-anon")


def test_osrm_distanze_in_cache(monkeypatch):
    fm._osrm_table.cache_clear()
    chiamate = []

    def finto_get(url, params=None, timeout=None):
        chiamate.append((url, params))
        return _RispostaJSON(200, {"code": "Ok", "distances": [[0, 1500.0, None]]})

    monkeypatch.setattr(fm.requests, "get", finto_get)
    origine, dest = (43.23, 12.78), [(43.24, 12.79), (43.25, 12.80)]
    assert fm.get_osrm_distances(origine, dest) == [1.5, None]
    assert fm.get_osrm_distances(origine, dest) == [1.5, None]
    assert len(chiamate) == 1  # la seconda volta risponde la cache
    assert chiamate[0][1]["annotations"] == "distance"  # senza, OSRM restituisce solo i tempi


def test_osrm_errore_non_in_cache(monkeypatch):
    fm._osrm_table.cache_clear()
    fm._osrm_route.cache_clear()  # in CI la rete c'è: un test prima può aver già messo in memoria un percorso vero
    chiamate = []

    def finto_get(url, params=None, timeout=None):
        chiamate.append(url)
        return _RispostaJSON(503, {})

    monkeypatch.setattr(fm.requests, "get", finto_get)
    origine, dest = (43.23, 12.78), [(43.24, 12.79)]
    assert fm.get_osrm_distances(origine, dest) == [None]
    assert fm.get_osrm_distances(origine, dest) == [None]
    assert fm.get_osrm_route(origine, dest[0]) == []
    assert len(chiamate) == 1  # dopo un errore OSRM resta in pausa per qualche minuto: niente nuove chiamate
    osrm.riprendi()
    assert fm.get_osrm_distances(origine, dest) == [None]
    assert len(chiamate) == 2  # finita la pausa si riprova (l'errore non è rimasto in memoria)


def test_osrm_in_pausa_usa_la_memoria(monkeypatch):
    fm._osrm_table.cache_clear()
    monkeypatch.setattr(fm.requests, "get", lambda *a, **k: _RispostaJSON(200, {"code": "Ok", "distances": [[0, 2000.0]]}))
    origine, dest = (43.23, 12.78), [(43.24, 12.79)]
    assert fm.get_osrm_distances(origine, dest) == [2.0]
    monkeypatch.setattr(fm.requests, "get", lambda *a, **k: _RispostaJSON(503, {}))
    assert fm.get_osrm_distances(origine, [(43.3, 12.9)]) == [None]  # errore: pausa
    assert fm.get_osrm_distances(origine, dest) == [2.0]  # in pausa, ma questa risposta era già in memoria


def test_osrm_route(monkeypatch):
    fm._osrm_route.cache_clear()
    coordinate_finte = [[12.78, 43.23], [12.785, 43.235], [12.79, 43.24]]
    risposta = _RispostaJSON(200, {"code": "Ok", "routes": [{"geometry": {"coordinates": coordinate_finte}}]})
    monkeypatch.setattr(fm.requests, "get", lambda *a, **k: risposta)
    route = fm.get_osrm_route((43.23, 12.78), (43.24, 12.79))
    assert route == coordinate_finte


def test_osrm_route_errore(monkeypatch):
    fm._osrm_route.cache_clear()
    monkeypatch.setattr(fm.requests, "get", lambda *a, **k: _RispostaJSON(500, {}))
    assert fm.get_osrm_route((43.23, 12.78), (43.24, 12.79)) == []


def test_fetch_brent_yf(monkeypatch):
    import sys
    from unittest.mock import MagicMock

    date_idx = pd.date_range("2026-09-01", "2026-10-10", freq="D")
    serie_finta = pd.Series(75.0, index=date_idx)
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = pd.DataFrame({"Close": serie_finta})

    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = mock_ticker
    monkeypatch.setitem(sys.modules, "yfinance", mock_yf)

    res = fm.fetch_brent_yf(7)
    assert res["b_t"] == pytest.approx(75.0)
    assert res["fx_t"] == pytest.approx(75.0)
    assert res["data_t"] == pd.Timestamp("2026-10-10")


def test_coordinate_sospette():
    righe = [
        # comune con 4 distributori, uno con le coordinate di Milano: solo quello è sospetto
        ("A1", "FINALE EMILIA", "MO", 44.833, 11.294), ("A2", "FINALE EMILIA", "MO", 44.840, 11.300),
        ("A3", "FINALE EMILIA", "MO", 44.825, 11.280), ("A4", "FINALE EMILIA", "MO", 45.4642, 9.19),
        # Roma: distributori a ~25 km dal centro (Ostia) restano
        ("R1", "ROMA", "RM", 41.90, 12.50), ("R2", "ROMA", "RM", 41.89, 12.48), ("R3", "ROMA", "RM", 41.73, 12.28),
        # due soli distributori a più di 50 km l'uno dall'altro: non si sa quale sia giusto, via tutti e due
        ("M1", "MONGHIDORO", "BO", 44.2168, 11.3216), ("M2", "MONGHIDORO", "BO", 41.8109, 12.3330),
        # due soli vicini: restano
        ("L1", "LIPARI", "ME", 38.4673, 14.9547), ("L2", "LIPARI", "ME", 38.5590, 14.8340),
        # un solo distributore: conta la provincia (Bologna), a più di 200 km = sospetto
        ("B1", "BOLOGNA", "BO", 44.494, 11.343), ("B2", "IMOLA", "BO", 44.353, 11.714),
        ("B3", "CASTEL SAN PIETRO TERME", "BO", 44.398, 11.589), ("B4", "PORRETTA", "BO", 40.85, 14.27),
    ]
    anag = pd.DataFrame(righe, columns=["id", "comune", "provincia", "lat", "lon"])
    sospette = set(anag.loc[fm.coordinate_sospette(anag), "id"])
    assert sospette == {"A4", "M1", "M2", "B4"}
    assert not fm.coordinate_sospette(anag.iloc[0:0]).any()
