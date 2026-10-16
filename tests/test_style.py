from unittest.mock import patch

import style


def test_colophon():
    with patch("style.html") as mock_html:
        style.colophon()
        mock_html.assert_called_once()
        html_arg = mock_html.call_args[0][0]
        assert "sCore lab" in html_arg
        assert "v1.0" in html_arg
        assert "Tutti i diritti riservati" in html_arg
        assert "x-colophon" in html_arg


def test_cerchio_progresso():
    html_0 = style.cerchio_progresso(0, "Inizio")
    assert "0%" in html_0
    assert "Inizio" in html_0
    assert "x-progress-box" in html_0

    html_50 = style.cerchio_progresso(50, "A metà")
    assert "50%" in html_50
    assert "A metà" in html_50

    html_100 = style.cerchio_progresso(100)
    assert "100%" in html_100


def test_verdetto_dello_stesso_colore_del_cerchio():
    """Il verdetto del «Consiglio» ha il colore del cerchio dello score: rosso solo con «Aspetta»."""
    for esito, colore in ((1, style.VERDE), (0, style.VERDE), (-1, style.ROSSO)):
        assert f'stroke="{colore}"' in style.cerchio_score(esito, "x")
        with patch("style.html") as mock_html:
            style.hero("Consiglio", "x", colore=style.colore_score(esito))
            assert f'<span class="v" style="color:{colore}">' in mock_html.call_args[0][0]
    with patch("style.html") as mock_html:  # senza colore: il giallo del CSS
        style.hero("Consiglio", "Rifornisci")
        assert '<span class="v">' in mock_html.call_args[0][0]


def test_verdetto_senza_score_negli_stessi_colori():
    """Senza score: «Rifornisci» verde, «Non conviene» rosso (come «Aspetta»)."""
    import pandas as pd

    from ui.hero_view import HeroView

    edges = pd.DataFrame({"score": [1.0]})
    for consiglio, titolo, colore in ((True, "Rifornisci", style.VERDE), (False, "Non conviene", style.ROSSO)):
        info = {"riserva": False, "consiglio": consiglio, "motivo": "il risparmio migliore"}
        with patch("style.html") as mock_html:
            HeroView(None, None, edges, info, None, "non configurato|SUPABASE_URL|nessuno", [])._render()
            testo = " ".join(c[0][0] for c in mock_html.call_args_list)
        assert f'<span class="v" style="color:{colore}">{titolo}</span>' in testo
