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
