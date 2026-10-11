"""Risoluzione della configurazione e dei secrets di Streamlit."""
from __future__ import annotations

import os

import streamlit as st

NOMI_URL = ("supabase_url", "url")
NOMI_CHIAVE = ("supabase_anon_key", "supabase_publishable_key", "supabase_key", "anon_key",
               "publishable_key", "key")


def _segreti_piatti() -> dict[str, str]:
    """Tutti i Secrets di Streamlit come {«sezione.nome» in minuscolo: valore}, sezioni annidate comprese."""
    try:
        segreti = dict(st.secrets)
    except Exception:  # nessun file dei segreti
        return {}
    piatti: dict[str, str] = {}

    def visita(d, prefisso: str) -> None:
        for k, v in d.items():
            nome = f"{prefisso}{str(k).strip().lower()}"
            if hasattr(v, "items"):
                visita(v, nome + ".")
            elif isinstance(v, str):
                piatti[nome] = v.strip()

    visita(segreti, "")
    return piatti


def supabase_config() -> tuple[str, str, list[str]]:
    """(indirizzo, chiave pubblica, nomi dei Secrets presenti) di Supabase.

    Cerca, senza badare a maiuscole e minuscole, SUPABASE_URL e SUPABASE_ANON_KEY (o SUPABASE_KEY,
    SUPABASE_PUBLISHABLE_KEY) in cima ai Secrets o nelle variabili d'ambiente, oppure url e anon_key (o key)
    in una sezione che nel nome contiene «supabase», come [supabase] o [connections.supabase]."""
    piatti = _segreti_piatti()

    def cerca(nomi: tuple[str, ...]) -> str:
        for n in nomi:  # in cima ai Secrets o nell'ambiente: solo i nomi completi SUPABASE_…
            if not n.startswith("supabase_"):
                continue
            v = piatti.get(n) or os.environ.get(n.upper(), "").strip()
            if v:
                return v
        for n in nomi:  # dentro una sezione «supabase»
            for chiave, v in piatti.items():
                sezione, _, nome = chiave.rpartition(".")
                if v and nome == n and "supabase" in sezione:
                    return v
        return ""

    return cerca(NOMI_URL), cerca(NOMI_CHIAVE), sorted(piatti)
