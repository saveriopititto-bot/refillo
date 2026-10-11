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
