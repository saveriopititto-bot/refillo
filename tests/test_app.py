"""Prova dell'interfaccia: apre app.py con dati finti (niente rete) e controlla che le schede si disegnino senza errori.

I selettori CSS e i contenitori dipendono da Streamlit: se un aggiornamento rompe la pagina, qui fallisce."""
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pytest
import streamlit_js_eval
from streamlit.testing.v1 import AppTest

import clients.osrm as osrm
import fuel_model as fm
import ui.data_service as ds
from tests.test_fuel_model import ANAG, PREZZI

APP = str(Path(__file__).resolve().parent.parent / "app.py")
GPS = {"coords": {"latitude": 43.23, "longitude": 12.79, "accuracy": 10}}


def _js(js_expressions=None, key=None):
    """streamlit_js_eval finto: il GPS risponde subito (chiave geo_0), la posizione dall'IP non serve."""
    return GPS if key and key.startswith("geo_") and key != "geo_ip" else None


@contextmanager
def _senza_rete():
    file = {fm.ANAG_FILE: ANAG.encode(), fm.PREZZI_FILE: PREZZI.encode()}
    with mock.patch.object(fm, "download_dati", side_effect=lambda name, **k: file[name]), \
            mock.patch.object(fm, "download_csv", side_effect=RuntimeError("niente rete nei test")), \
            mock.patch.object(ds, "dati_freschi", return_value=True), \
            mock.patch.object(ds, "default_path", return_value=None), \
            mock.patch.object(fm, "fetch_brent_yf", side_effect=RuntimeError("niente rete nei test")), \
            mock.patch.object(fm, "fetch_brent_score", side_effect=RuntimeError("niente rete nei test")), \
            mock.patch("core.model.get_osrm_distances", side_effect=lambda o, d: [None] * len(d)), \
            mock.patch("core.model.get_osrm_minuti", side_effect=lambda o, d: [None] * len(d)), \
            mock.patch("core.model.get_osrm_route", return_value=[]), \
            mock.patch.object(streamlit_js_eval, "streamlit_js_eval", side_effect=_js):
        osrm.riprendi()
        ds.clear_all_caches()
        yield


def _testo(at: AppTest) -> str:
    return " ".join(m.value for m in at.markdown)


@pytest.fixture
def app():
    with _senza_rete():
        yield AppTest.from_file(APP, default_timeout=60)


def test_schermata_avvio(app):
    app.run()
    assert not app.exception
    assert [b.key for b in app.button] == ["avvia"]  # solo il pulsante del distributore
    assert 'class="x-lead"' not in _testo(app)  # niente Home prima del tocco


def test_home(app):
    app.session_state["avviato"] = True
    app.run()
    assert not app.exception
    testo = _testo(app)
    assert "Il distributore migliore" in testo
    assert testo.count('class="x-metric"') == 3  # prezzo medio, distributori, costo al km
    assert app.selectbox(key="carburante").value == "Benzina"
    assert 'class="x-progress-wrap' not in testo  # il cerchio di caricamento si è chiuso


def test_faq(app):
    app.session_state["avviato"] = True
    app.session_state["scheda"] = "F.A.Q."
    app.run()
    assert not app.exception
    assert "Come funziona" in _testo(app)
    assert len(app.dataframe) == 1  # la tabella degli archi
