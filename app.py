"""App Streamlit: pesi degli archi (posizione -> distributori) con lo score di rifornimento."""
from __future__ import annotations

import streamlit as st

import fuel_model as fm
import style
from ui.controls_view import ControlsView
from ui.data_service import leggi_brent_score
from ui.edges_view import EdgesView
from ui.hero_view import HeroView
from ui.how_view import HowView
from ui.result_view import ResultView

st.set_page_config(page_title="Conviene rifornire?", page_icon="⛽", layout="wide", initial_sidebar_state="collapsed")
style.apply_style()

c_hero = st.container()

# --------------------------------------------------------------------------
# Controlli utente e dati
# --------------------------------------------------------------------------
controls = ControlsView.render(c_hero=c_hero)

# --------------------------------------------------------------------------
# Calcolo
# --------------------------------------------------------------------------
edges, info = fm.compute_edges(controls.cands, controls.origin, controls.params)
bs, bs_err = leggi_brent_score()

# --------------------------------------------------------------------------
# Consiglio in evidenza (in cima)
# --------------------------------------------------------------------------
HeroView(controls.hero_testo, controls.hero_cerchio, edges, info, bs, bs_err, controls.note_dati).render()

# --------------------------------------------------------------------------
# Schede di dettaglio
# --------------------------------------------------------------------------
# La riga con le pillole (radio «scheda») sta in ControlsView; si disegna solo la scheda scelta.
# La tabella degli archi sta in «Come funziona».
if st.session_state.get("scheda", "Risultato") == "Risultato":
    with controls.contenuto:
        ResultView(
            edges=edges,
            info=info,
            origin=controls.origin,
            raggio=controls.raggio,
            ref_mode=controls.ref_mode,
            show_all_lines=controls.show_all_lines,
            fonte=controls.fonte,
        ).render()

else:
    with controls.contenuto:
        HowView(fonte=controls.fonte).render()
        EdgesView(edges=edges, origin=controls.origin).render()

# --------------------------------------------------------------------------
# Colofon
# --------------------------------------------------------------------------
style.colophon()
