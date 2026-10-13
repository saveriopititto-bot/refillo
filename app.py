"""App Streamlit: dove conviene fare rifornimento (solo coordinamento; il calcolo è in core/, le viste in ui/)."""
from __future__ import annotations

import streamlit as st

import fuel_model as fm
import style
from ui.controls_view import HOME, ControlsView
from ui.data_service import rileva_posizione
from ui import preferenze
from ui.edges_view import EdgesView
from ui.hero_view import HeroView
from ui.how_view import HowView
from ui.result_view import ResultView, render_top5

st.set_page_config(page_title="Conviene rifornire?", page_icon="⛽", layout="wide", initial_sidebar_state="collapsed")
style.apply_style()

c_hero = st.container()

# la posizione si chiede subito, già nella schermata d'avvio (sempre nello stesso punto della pagina, così la
# richiesta non riparte dopo il tocco): GPS e, se fallisce, indirizzo internet
posizione = rileva_posizione()
# anche le opzioni salvate nel browser alla visita precedente: quando si tocca il pulsante sono già pronte
preferenze.leggi()

# all'apertura solo il pulsante del distributore: i download partono quando lo si tocca
if not st.session_state.get("avviato"):
    style.avvio(fm.FUELS)
    st.stop()

# --------------------------------------------------------------------------
# Controlli utente e dati
# --------------------------------------------------------------------------
controls = ControlsView.render(c_hero=c_hero, posizione=posizione)

# --------------------------------------------------------------------------
# Calcolo
# --------------------------------------------------------------------------
controls.caricamento.mostra(98, "Calcolo le distanze su strada…")
edges, info = fm.compute_edges(controls.cands, controls.origin, controls.params)

# --------------------------------------------------------------------------
# Consiglio in evidenza (in cima)
# --------------------------------------------------------------------------
HeroView(controls.hero_testo, controls.hero_cerchio, edges, info, controls.bs, controls.bs_err, controls.note_dati,
         controls.nota_posizione).render()

# --------------------------------------------------------------------------
# Schede di dettaglio
# --------------------------------------------------------------------------
with controls.top5:
    render_top5(edges, controls.unita)

# La riga con le pillole Home / F.A.Q. sta in ControlsView; si disegna solo la scheda scelta.
# La tabella degli archi sta in «F.A.Q.».
if st.session_state.get("scheda", HOME) == HOME:
    with controls.contenuto:
        ResultView(
            edges=edges,
            info=info,
            origin=controls.origin,
            raggio=controls.raggio,
            ref_mode=controls.ref_mode,
            show_all_lines=controls.show_all_lines,
            fonte=controls.fonte,
            unita=controls.unita,
            metriche=controls.metriche,
            valore_tempo=controls.params.valore_tempo,
        ).render()

else:
    with controls.contenuto:
        HowView(fonte=controls.fonte, esclusi=controls.esclusi).render()
        EdgesView(edges=edges, origin=controls.origin, unita=controls.unita).render()

# --------------------------------------------------------------------------
# Colofon
# --------------------------------------------------------------------------
style.colophon()

# pagina completa: si chiude il cerchio (prima la pagina si vedrebbe a metà, per esempio mentre risponde OSRM)
controls.caricamento.chiudi()
st.session_state["pronta"] = True
preferenze.salva()
