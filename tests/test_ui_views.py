import gzip

import pandas as pd
from ui.data_service import nota_score, perche_petrolio
from ui.edges_view import EdgesView
from ui.how_view import HowView
from ui.result_view import ResultView


def test_perche_petrolio():
    assert "Tra pochi giorni anche il carburante costerà di più" in perche_petrolio({"esito": 1})
    assert "La benzina non cambierà molto" in perche_petrolio({"esito": 0})
    assert "anche la benzina costerà di meno" in perche_petrolio({"esito": -1})


def test_nota_score():
    nota_err = nota_score("timeout connessione")
    assert "non raggiungibile" in nota_err
    assert "timeout connessione" in nota_err

    nota_cfg = nota_score("non configurato|SUPABASE_URL|nessuno")
    assert "non configurato" in nota_cfg
    assert "SUPABASE_URL" in nota_cfg


def test_how_view_init():
    hv = HowView(fonte="Dati MIMIT")
    assert hv.fonte == "Dati MIMIT"


def test_edges_view_empty_no_error(monkeypatch):
    import style
    called = []
    monkeypatch.setattr(style, "error_card", lambda msg: called.append(msg))
    ev = EdgesView(edges=pd.DataFrame(), origin=(43.0, 12.0))
    ev.render()
    assert len(called) == 1
    assert "Nessun arco da mostrare" in called[0]


def test_result_view_empty_no_error(monkeypatch):
    import style
    called = []
    monkeypatch.setattr(style, "error_card", lambda msg: called.append(msg))
    rv = ResultView(
        edges=pd.DataFrame(),
        info={},
        origin=(43.0, 12.0),
        raggio=20,
        litri=None,
        ref_mode="mediana",
        show_all_lines=False,
        fonte="test",
    )
    rv.render()
    assert len(called) == 1
    assert "Nessun distributore da mostrare" in called[0]


def test_get_mimit_dataset_with_progress(monkeypatch):
    import ui.data_service as ds

    ds.clear_all_caches()
    progress_updates = []

    class MockProgress:
        def markdown(self, text, unsafe_allow_html=False):
            progress_updates.append(text)

    fake_anag = b"id;nome;lat;lon;comune\n1;Dist;43.1;12.1;Roma"
    fake_prezzi = b"id;carburante;prezzo;isSelf\n1;Benzina;1.75;1"

    monkeypatch.setattr(ds.fm, "download_csv", lambda name, timeout=60.0, on_progress=None: (
        fake_anag if "anagrafica" in name else fake_prezzi
    ))
    monkeypatch.setattr(ds.fm, "download_dati", lambda name, timeout=30.0, on_progress=None: (
        b"Estrazione del 2000-01-01\n" + (fake_anag if "anagrafica" in name else fake_prezzi)  # vecchia: scartata
    ))

    c_progress = MockProgress()
    (anag_b, src_a), (prezzi_b, src_p) = ds.get_mimit_dataset(c_progress=c_progress)

    assert anag_b == fake_anag
    assert prezzi_b == fake_prezzi
    assert src_a == "scaricato"
    assert src_p == "scaricato"
    assert len(progress_updates) > 0
    assert any("0%" in p for p in progress_updates)
    assert any("100%" in p for p in progress_updates)


def test_script_aggiorna_mimit(monkeypatch, tmp_path):
    import scripts.aggiorna_mimit as am
    from tests.test_fuel_model import ANAG, PREZZI

    fake_anag = ANAG.encode()
    fake_prezzi = PREZZI.encode()

    monkeypatch.setattr(am.fm, "download_csv", lambda name, timeout=60.0, on_progress=None: (
        fake_anag if "anagrafica" in name else fake_prezzi
    ))

    dest = tmp_path / "test_data"
    ret = am.main(["--dest", str(dest)])

    assert ret == 0
    assert gzip.decompress((dest / f"{am.fm.ANAG_FILE}.gz").read_bytes()) == fake_anag
    assert gzip.decompress((dest / f"{am.fm.PREZZI_FILE}.gz").read_bytes()) == fake_prezzi


def test_get_mimit_dataset_usa_copia_dati_di_oggi(monkeypatch):
    import ui.data_service as ds

    ds.clear_all_caches()
    oggi = pd.Timestamp.now(tz="Europe/Rome")
    giorno = ds.ultimo_rilascio_mimit(oggi)
    copia = f"Estrazione del {giorno:%Y-%m-%d}\nid|x\n".encode()

    def mimit_non_serve(*a, **k):
        raise AssertionError("con la copia di oggi non si scarica dal MIMIT")

    monkeypatch.setattr(ds.fm, "download_csv", mimit_non_serve)
    monkeypatch.setattr(ds.fm, "download_dati", lambda name, timeout=30.0, on_progress=None: copia)
    (anag_b, src_a), (prezzi_b, src_p) = ds.get_mimit_dataset()
    assert anag_b == copia and prezzi_b == copia and src_a == src_p == "scaricato"
    ds.clear_all_caches()


def test_dati_freschi():
    from ui.data_service import dati_freschi

    alle_10 = pd.Timestamp("2026-10-11 10:00", tz="Europe/Rome")
    alle_8 = pd.Timestamp("2026-10-11 08:00", tz="Europe/Rome")
    assert dati_freschi(b"Estrazione del 2026-10-11\nid|x", alle_10)
    assert not dati_freschi(b"Estrazione del 2026-10-10\nid|x", alle_10)
    assert dati_freschi(b"Estrazione del 2026-10-10\nid|x", alle_8)  # prima delle 9 vale quella di ieri
    assert not dati_freschi(b"senza data\nid|x", alle_10)
