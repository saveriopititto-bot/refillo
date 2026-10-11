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

L'app pubblicata è https://refillo.streamlit.app/ (Streamlit Community Cloud, branch `main`, `app.py`,
Python 3.12): ogni merge su `main` la aggiorna da solo.

## Controlli

```bash
python -m pytest                      # test del modello
python -m compileall -q -x '/\.' .    # sintassi di tutti i file
```

- La CI (GitHub Actions) gira su Python **3.10** e 3.12. Niente sintassi solo 3.12+, come le f-string con
  le stesse virgolette annidate (`f"{d['k']}"` va bene, `f"{f'{x}'}"` dentro `f'...'` no).
- I test non importano `app.py`: per l'interfaccia prova l'app con `streamlit.testing.v1.AppTest`
  (simulando `fm.download_csv`, `fm.download_dati`, `fm.fetch_brent_yf`, `fm.fetch_brent_score`, `fm.get_osrm_distances`,
  `fm.get_osrm_route` e `streamlit_js_eval.get_geolocation`) e, per i cambi visivi, con Chromium/Playwright
  (Chromium in `/opt/pw-browsers`, da passare come `executable_path`).
- Nell'AppTest le schede si cambiano con `at.session_state["scheda"] = "F.A.Q."`; `st.cache_data` resta in
  memoria tra un AppTest e l'altro nello stesso processo, quindi per casi diversi usa argomenti diversi.
- Nell'ambiente di sviluppo cloud `www.mimit.gov.it` e Yahoo Finance sono bloccati dal proxy: il download
  reale va verificato sull'app online. Anche `router.project-osrm.org` (OSRM) è bloccato.

## Convenzioni

- **Interfaccia in italiano semplice**: niente simboli matematici né formule (la formula è solo nel
  README, sezione «Il modello», con la tabella nomi dell'app ↔ simboli). Numeri in formato italiano
  (`_it`, `eur`, `num` in `ui/formatters.py`); percentuali per livelli e pesi.
- **Stile**: `style.py` + `.streamlit/config.toml`, lo stesso di test4 (palette `#8ecae6` `#219ebc`
  `#023047` `#ffb703` `#fb8500`, font Archivo). Le schede sono `style.card(key)`, i blocchi HTML sono le
  funzioni di `style.py`. I selettori CSS si agganciano ad attributi interni di Streamlit (testati con la
  1.65; `requirements.txt` chiede `streamlit>=1.65`).
- **Pagina**: niente titolo. In cima il riquadro «Consiglio» (`style.hero_box`, contenitore `hero`), visibile in
  tutte le schede: testo a sinistra e, a destra, il cerchio dello score con sotto il menu del carburante. Sotto, un
  unico riquadro `style.card("schede")`: in cima la riga `comandi`, tutta a sinistra e in linea anche da
  telefono: Home · Posizione · Avanzate · F.A.Q. (tutte con lo sfondo tenue `N100`); poi il contenuto della scheda scelta. Home e F.A.Q. sono
  pulsanti a pillola (`nav_home`, `nav_faq`, quello aperto è `type="primary"`) che scrivono `st.session_state["scheda"]`
  (`HOME`, `FAQ` in `ui/controls_view.py`): `st.tabs` e `st.radio` non permettono altri comandi tra le pillole. Si
  disegna solo la scheda scelta. In Streamlit 1.65 le colonne sono `stColumn` e il menu a tendina è un `input` dentro
  `stSelectbox`. La tabella degli archi sta in fondo a
  «F.A.Q.» (la scheda Archi è stata tolta). Indicatori della Home: prezzo medio, distributori, costo al km
  (il riquadro «Litri da fare» è stato tolto). La scheda Petrolio (pagina di scorebrent) è stata tolta: non
  rimetterla.
- **Mappa**: Leaflet con `folium` (`ui/map_leaflet.py`, niente pydeck), inserita come HTML con
  `st.components.v1.html` dentro `st.container(key="mappa")`: niente `streamlit-folium`, così toccarla non fa
  ricaricare la pagina. Sempre in verticale, proporzione 2:3 (`aspect-ratio` sull'iframe in `style.py`), al massimo
  500 px di larghezza da computer, centrata; da telefono a tutta larghezza. Tile CARTO chiari dall'URL diretto
  (`TILES`: il nome `cartodbpositron` di folium ora chiede una chiave). Script caricati: solo Leaflet e jQuery (i
  popup di folium lo usano). Toccando un distributore si apre il popup con il link «Portami qui» (Google Maps).
  Nell'ambiente cloud i CDN e i tile sono bloccati: per provarla con Chromium servi `leaflet.js` e jQuery da npm con
  `context.route`.
- **Dati**: prezzi e anagrafica MIMIT da `ui/data_service.get_mimit_dataset`, con precedenza: CSV caricati a
  mano → cartella `data/` → copia nel branch `dati` (`fm.download_dati`, `mimit/*.csv.gz`, solo se la data di
  estrazione + 1 giorno è quella dell'ultimo aggiornamento delle 9:00: il MIMIT data i file con il giorno prima) → sito MIMIT (`fm.download_csv`); i file scaricati
  restano in memoria fino alle 9:00 successive. La copia la salva ogni mattina `.github/workflows/aggiorna_mimit.yml`
  (`scripts/aggiorna_mimit.py`) nel branch `dati`: i CSV MIMIT non vanno mai su `main` e non si versionano.
  Brent da Yahoo Finance (`fetch_brent_yf`, cache 3 ore). `load_data` tiene al massimo 2 versioni dei CSV (`max_entries=2`).
  `parse_anagrafica` resta con il ciclo Python: la versione con `read_csv` è stata misurata ed è più lenta.
- **OSRM**: distanze su strada per i 99 distributori più vicini (`/table` con `annotations=distance`, senza
  OSRM restituisce solo i tempi) e percorso del migliore (`/route`). Le risposte riuscite restano in memoria
  (`lru_cache`), gli errori no; se OSRM non risponde si usa la linea d'aria × fattore strada.
- **Storico**: `storico.py` + `scripts/raccogli_storico.py`, lanciati ogni mattina da
  `.github/workflows/storico.yml`, che salva `storico/medie_comuni.csv.gz` (mediane per comune, ultimi 40
  giorni) e `storico/comuni.csv.gz` nel branch `dati`. Non fare mai merge del branch `dati` in `main` e non
  modificarlo a mano. Le azioni programmate girano solo se il loro file è su `main`.
- **Score 30 giorni (1 / 0 / -1)**: in sviluppo sul branch `claude/score-30gg`, **senza merge** su `main`
  finché l'utente non lo chiede (eccezione al flusso di lavoro qui sopra).
- **Score del petrolio**: `fuel_model.fetch_brent_score` legge l'ultima riga della tabella `brent_score` di
  Supabase, scritta ogni giorno dal repository `scorebrent`. Usa la chiave pubblica: segreti `SUPABASE_URL` e
  `SUPABASE_ANON_KEY` nei Secrets di Streamlit, mai la `service_role`. Lo score decide il riquadro
  «Consiglio» (Conviene / Rifornisci / Aspetta, con il cerchio), ma non entra nel calcolo del risparmio né nella
  classifica; senza score il riquadro torna al verdetto sul risparmio, con una riga che dice perché manca
  (segreto mancante o Supabase non raggiungibile). Con lo score, `PERCHE_PETROLIO` in `ui/data_service.py` spiega il
  consiglio con le frasi scelte dall'utente (non cambiarle senza chiedere). Nei test va simulato `fm.fetch_brent_score`.
- **Calcolo** (`compute_edges`): i km in più sono sempre andata e ritorno (la destinazione è stata tolta).
  `score` = risparmio sul prezzo + effetto Brent − costo del viaggio: decide classifica e verdetto.
  `risparmio` = lo stesso senza l'effetto Brent: è quello mostrato nella frase, sulla mappa e nei 5 migliori
  (l'effetto Brent è uguale per tutti e non è un risparmio vero). Costo al km = consumo × prezzo di mercato +
  usura. Il test `test_compute_edges_conti_a_mano` rifà i conti a mano: aggiornalo se cambi la formula.
- **Riserva**: sotto la soglia di riserva il «Consiglio» dice sempre «Rifornisci», anche se lo score del
  petrolio dice altro (`info["riserva"]`).
- La logica del modello sta in `core/`, `ingestion/` e `clients/` (riesportati da `fuel_model.py`, che i test e
  l'app importano come `fm`); l'interfaccia sta in `app.py` (solo coordinamento) e nelle viste di `ui/`.
