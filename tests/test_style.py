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
