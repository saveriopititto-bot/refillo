# ⛽ Score di rifornimento

App Streamlit che, data la posizione dell'auto, assegna un punteggio ai distributori vicini
(open data MIMIT) e dice dove — e se — conviene fare rifornimento.

$$S_i = q\,[(P_{market}-P_i) + \alpha\,P_{market}\,\Delta B] - D_i\,C_{km}$$

## Avvio

```bash
pip install -r requirements.txt
streamlit run app.py
```

Metti i CSV MIMIT in `data/` (vedi `data/README.md`) oppure caricali dalla barra laterale.

## Struttura

- `fuel_model.py` — lettura dei CSV, geometria, Brent e calcolo degli score.
- `app.py` — interfaccia Streamlit (mappa pydeck, tabella degli archi, export CSV).
- `tests/` — test del modello: `pip install pytest && pytest`.
