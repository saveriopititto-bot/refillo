# ⛽ Score di rifornimento

App Streamlit che, data la posizione dell'auto, assegna un punteggio ai distributori vicini
(open data MIMIT) e dice dove — e se — conviene fare rifornimento.

$$S_i = q\,[(P_{market}-P_i) + \alpha\,P_{market}\,\Delta B] - D_i\,C_{km}$$

## Avvio

```bash
pip install -r requirements.txt
streamlit run app.py
```

All'avvio l'app scarica da sola i CSV aggiornati dal sito del MIMIT (con una cache di 3 ore e il pulsante
"Riscarica ora"). In alternativa si possono caricare a mano dalla barra laterale o mettere in `data/`
(vedi `data/README.md`): i file caricati a mano hanno la precedenza, poi quelli in `data/`, poi il download.

## Struttura

- `fuel_model.py` — lettura dei CSV, geometria, Brent e calcolo degli score.
- `app.py` — interfaccia Streamlit: schede Risultato (verdetto, mappa pydeck, migliori 5), Archi (tabella ed export CSV), Come funziona.
- `style.py` + `.streamlit/config.toml` — stile dell'interfaccia, lo stesso di test4 (layout "1a": navigazione a pillole, schede bianche arrotondate, palette `#8ecae6` `#219ebc` `#023047` `#ffb703` `#fb8500`, font Archivo). I selettori CSS si agganciano ad attributi interni di Streamlit (testati con la 1.65).
- `tests/` — test del modello: `pip install pytest && python -m pytest` (eseguiti anche in CI con GitHub Actions a ogni push e PR).
