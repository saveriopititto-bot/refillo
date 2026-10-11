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
    assert (dest / am.fm.ANAG_FILE).read_bytes() == fake_anag
    assert (dest / am.fm.PREZZI_FILE).read_bytes() == fake_prezzi
