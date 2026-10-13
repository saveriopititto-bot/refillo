"""Le opzioni scelte restano nel browser di chi usa l'app (localStorage, niente account): alla visita dopo le ritrova.

Non si salvano il livello del serbatoio e i litri da fare, che cambiano a ogni rifornimento. I valori letti dal
browser si controllano (tipo e intervallo) prima di usarli: un valore strano viene ignorato, non rompe la pagina."""
from __future__ import annotations

import json
import zlib

import streamlit as st
import streamlit_js_eval

import fuel_model as fm

CHIAVE_BROWSER = "refillo_opzioni"
# chiave del widget: (valore predefinito, minimo, massimo) per i numeri, (predefinito, scelte) per gli altri
OPZIONI: dict[str, tuple] = {
    "opt_raggio": (20, 2, 60),
    "opt_riserva": (10, 0, 50),
    "opt_self": ("Self", ("Self", "Servito")),
    "opt_osrm": (True, (True, False)),
    "opt_linee": (False, (True, False)),
    "opt_usura": (0.05, 0.0, 1.0),
    "opt_tempo": (10.0, 0.0, 100.0),
    "opt_autostrade": (False, (True, False)),
    "opt_eta": (5, 1, 60),
    "opt_strada": (1.3, 1.0, 2.0),
    "opt_rif": ("mediana", ("mediana", "media")),
    "opt_soglia": (0.0, -1000.0, 1000.0),
    "opt_alpha": (20, 0, 40),
    "carburante": (fm.FUELS[0], tuple(fm.FUELS)),
}
# serbatoio e consumo hanno una chiave per carburante (i predefiniti sono in ui/controls_view.PREDEFINITI)
PER_CARBURANTE = {"v_tot": (5.0, 200.0), "consumo": (1.0, 40.0)}


def _regola(chiave: str) -> tuple | None:
    if chiave in OPZIONI:
        return OPZIONI[chiave]
    nome, _, fuel = chiave.rpartition("_")
    if nome in PER_CARBURANTE and fuel in fm.FUELS:
        return (None, *PER_CARBURANTE[nome])
    return None


def valida(dati) -> dict:
    """Solo le opzioni conosciute, con il tipo giusto e dentro l'intervallo dei loro widget."""
    if not isinstance(dati, dict):
        return {}
    buone = {}
    for chiave, valore in dati.items():
        regola = _regola(chiave)
        if regola is None:
            continue
        predefinito = regola[0]
        if len(regola) == 2:  # scelte
            if valore in regola[1] and type(valore) is type(regola[1][0]):
                buone[chiave] = valore
            continue
        lo, hi = regola[1], regola[2]
        if isinstance(valore, bool) or not isinstance(valore, (int, float)) or not lo <= valore <= hi:
            continue
        # gli slider interi vogliono un int, i campi numerici un float (come i loro predefiniti)
        buone[chiave] = int(valore) if isinstance(predefinito, int) and float(valore).is_integer() else float(valore)
    return buone


def valore(chiave: str, predefinito):
    """Valore iniziale di un widget: quello salvato nel browser, se c'è, altrimenti il predefinito.

    Si passa come `value=` / `index=` del widget: scrivere le chiavi dei widget nella sessione non basta, perché i
    widget dentro «Opzioni» (un popover) si disegnano dopo e partirebbero dal minimo."""
    return st.session_state.get("_preferenze", {}).get(chiave, predefinito)


def leggi() -> None:
    """Chiede al browser le opzioni salvate (una volta per sessione) e le tiene in `_preferenze`.

    Va chiamata in cima ad app.py, già nella schermata d'avvio: quando si tocca il pulsante sono già pronte."""
    if st.session_state.get("opzioni_lette"):
        return
    testo = streamlit_js_eval.streamlit_js_eval(
        js_expressions=f"localStorage.getItem('{CHIAVE_BROWSER}') || ''", key="opzioni_leggi")
    if testo is None:  # il browser non ha ancora risposto
        return
    try:
        salvate = valida(json.loads(testo)) if testo else {}
    except (TypeError, ValueError):
        salvate = {}
    st.session_state["_preferenze"] = dict(salvate)
    st.session_state["opzioni_lette"] = True
    # il menu della schermata d'avvio c'è già (la risposta arriva dopo): qui, prima che si ridisegni, si può cambiare
    if "carburante" in salvate and not st.session_state.get("avviato"):
        st.session_state["carburante_avvio"] = salvate["carburante"]


def salva() -> None:
    """Salva nel browser le opzioni attuali, solo dopo averle lette (per non cancellarle con i predefiniti)."""
    if not st.session_state.get("opzioni_lette"):
        return
    # le chiavi dei carburanti non mostrati spariscono dalla sessione: si tengono quelle già note
    pref = dict(st.session_state.get("_preferenze", {}))
    attuali = {k: v for k, v in st.session_state.items() if isinstance(k, str) and _regola(k)}
    if st.session_state.get("_carburante"):  # la scelta del carburante vive in «_carburante» (vedi ControlsView)
        attuali["carburante"] = st.session_state["_carburante"]
    pref.update(valida(attuali))
    st.session_state["_preferenze"] = pref
    testo = json.dumps(pref, sort_keys=True)
    # la chiave cambia solo quando cambiano le opzioni: il browser scrive una volta per ogni cambio
    streamlit_js_eval.streamlit_js_eval(
        js_expressions=f"localStorage.setItem('{CHIAVE_BROWSER}', {json.dumps(testo)}); 1",
        key=f"opzioni_salva_{zlib.crc32(testo.encode()):08x}")
