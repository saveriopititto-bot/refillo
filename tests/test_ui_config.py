from unittest.mock import patch

from ui.config import supabase_config


def test_supabase_config_da_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://env.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key-123")
    with patch("streamlit.secrets", {}):
        url, chiave, _trovati = supabase_config()
        assert url == "https://env.supabase.co"
        assert chiave == "anon-key-123"


def test_supabase_config_da_secrets(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    segreti = {
        "supabase": {
            "url": "https://sec.supabase.co",
            "anon_key": "sec-anon-456",
        }
    }
    with patch("streamlit.secrets", segreti):
        url, chiave, trovati = supabase_config()
        assert url == "https://sec.supabase.co"
        assert chiave == "sec-anon-456"
        assert "supabase.url" in trovati
