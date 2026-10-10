# CLAUDE.md

Istruzioni per Claude Code su questo repository. Rispondi all'utente in italiano.

## Flusso di lavoro (deciso dall'utente)

Per ogni modifica richiesta:

1. Riparti dal `main` aggiornato (le PR precedenti vengono unite subito).
2. Fai la modifica e, nella stessa PR, aggiorna `README.md` se la modifica cambia qualcosa che vi è
   descritto (funzioni, interfaccia, impostazioni, valori predefiniti, struttura).
3. Verifica prima del push (vedi «Controlli»).
4. Apri la PR verso `main`, seguila e, appena la CI è verde, fai il merge **senza chiedere conferma**.
5. Scrivi all'utente una volta sola, a merge fatto: cosa è cambiato e cosa controllare sull'app online.

Se un test fallisce, correggilo prima del merge. Se la richiesta è ambigua o la modifica è rischiosa
(cambia i calcoli, rimuove funzioni, tocca i dati), chiedi prima di procedere.

L'app pubblicata è https://fuelmode.streamlit.app/ (Streamlit Community Cloud, branch `main`, `app.py`,
Python 3.12): ogni merge su `main` la aggiorna da solo.

## Controlli

```bash
python -m pytest                      # test del modello
python -m compileall -q -x '/\.' .    # sintassi di tutti i file
```

- La CI (GitHub Actions) gira su Python **3.10** e 3.12. Niente sintassi solo 3.12+, come le f-string con
  le stesse virgolette annidate (`f"{d['k']}"` va bene, `f"{f'{x}'}"` dentro `f'...'` no).
- I test non importano `app.py`: per l'interfaccia prova l'app con `streamlit.testing.v1.AppTest`
  (simulando `fm.download_csv`, `fm.fetch_brent_yf` e `streamlit_js_eval.get_geolocation`) e, per i
  cambi visivi, con Chromium/Playwright.
- Nell'ambiente di sviluppo cloud `www.mimit.gov.it` e Yahoo Finance sono bloccati dal proxy: il download
  reale va verificato sull'app online.

## Convenzioni

- **Interfaccia in italiano semplice**: niente simboli matematici né formule (la formula è solo nel
  README, sezione «Il modello», con la tabella nomi dell'app ↔ simboli). Numeri in formato italiano
  (`_it`, `eur`, `num` in `app.py`); percentuali per livelli e pesi.
- **Stile**: `style.py` + `.streamlit/config.toml`, lo stesso di test4 (palette `#8ecae6` `#219ebc`
  `#023047` `#ffb703` `#fb8500`, font Archivo). Le schede sono `style.card(key)`, i blocchi HTML sono le
  funzioni di `style.py`. I selettori CSS si agganciano ad attributi interni di Streamlit (testati con la
  1.65).
- **Dati**: prezzi e anagrafica MIMIT scaricati da `fuel_model.download_csv` (cache 3 ore), Brent da Yahoo
  Finance (`fetch_brent_yf`, cache 3 ore). Precedenza: CSV caricati a mano → cartella `data/` → download.
  I CSV in `data/` non si versionano.
- **Storico**: `storico.py` + `scripts/raccogli_storico.py`, lanciati ogni mattina da
  `.github/workflows/storico.yml`, che salva `storico/medie_comuni.csv.gz` (mediane per comune, ultimi 40
  giorni) e `storico/comuni.csv.gz` nel branch `dati`. Non fare mai merge del branch `dati` in `main` e non
  modificarlo a mano. Le azioni programmate girano solo se il loro file è su `main`.
- **Score 30 giorni (1 / 0 / -1)**: in sviluppo sul branch `claude/score-30gg`, **senza merge** su `main`
  finché l'utente non lo chiede (eccezione al flusso di lavoro qui sopra).
- La logica del modello sta in `fuel_model.py`; `app.py` è solo interfaccia.
