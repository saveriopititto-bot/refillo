from ui import preferenze


def test_valida_tiene_solo_opzioni_buone():
    salvate = {
        "opt_raggio": 35, "opt_tempo": 0, "opt_self": "Servito", "opt_osrm": False, "carburante": "GPL",
        "v_tot_GPL": 45, "consumo_Metano": 4.5,
        "opt_eta": 999,           # fuori intervallo
        "opt_strada": "1,3",      # tipo sbagliato
        "opt_autostrade": 1,      # non è un sì/no
        "carburante_x": "Benzina", "v_tot_Diesel": 50, "livello": 30,  # chiavi sconosciute
    }
    assert preferenze.valida(salvate) == {
        "opt_raggio": 35, "opt_tempo": 0.0, "opt_self": "Servito", "opt_osrm": False, "carburante": "GPL",
        "v_tot_GPL": 45.0, "consumo_Metano": 4.5,
    }
    assert isinstance(preferenze.valida({"opt_raggio": 35.0})["opt_raggio"], int)  # gli slider interi vogliono int


def test_valida_dati_non_validi():
    assert preferenze.valida(None) == {} and preferenze.valida([1, 2]) == {} and preferenze.valida("x") == {}


def test_predefiniti_dentro_gli_intervalli():
    predefiniti = {k: r[0] for k, r in preferenze.OPZIONI.items()}
    assert preferenze.valida(predefiniti) == predefiniti
