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
- `tests/test_app.py` apre `app.py` con `AppTest` e dati finti (niente rete) e controlla schermata d'avvio, Home e
  F.A.Q.: aggiornalo se cambi la struttura della pagina. Gli altri test non importano `app.py`: per provare
  l'interfaccia a mano usa `streamlit.testing.v1.AppTest`
  (simulando `fm.download_csv`, `fm.download_dati`, `fm.fetch_brent_yf`, `fm.fetch_brent_score`, `fm.get_osrm_distances`,
  `fm.get_osrm_route`, `fm.get_osrm_minuti` (in `core.model`), `streamlit_js_eval.streamlit_js_eval`: chiave `geo_0` per il GPS, `geo_ip` per la posizione dall'IP) e, per i cambi visivi, con Chromium/Playwright
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
  1.65; `requirements.txt` fissa `streamlit~=1.65.0`: Streamlit Cloud non deve installare da solo una versione nuova
  che rompe lo stile; per aggiornarla alza la versione, prova con Playwright e aggiorna i selettori).
- **Pagina**: niente titolo. In cima il riquadro «Consiglio» (`style.hero_box`, contenitore `hero`), visibile in
  tutte le schede: testo a sinistra e, a destra, il cerchio dello score (90 px, 68 da telefono; verde, rosso solo con «Aspetta»; il verdetto ha lo
  stesso colore, `style.colore_score`; senza score «Rifornisci» verde e «Non conviene» rosso). Sotto, un
  unico riquadro `style.card("schede")`: in cima la riga `comandi`, sempre su una riga anche da telefono: Home ·
  Posizione · Opzioni · Top 5 · F.A.Q., cinque pillole della stessa larghezza (colonne `flex: 1 1 0`, pulsanti
  `width="stretch"`) con lo sfondo tenue `N100` e testo senza grassetto. Opzioni e Top 5 sono `st.popover`
  (restano aperti mentre si cambiano i valori; il corpo `stPopoverBody` sta fuori dalla riga, quindi le sue regole
  CSS non vanno sotto `.st-key-comandi`); il Top 5 si riempie in `app.py` con `render_top5`. Da telefono la freccia
  dei popover è nascosta; poi il contenuto della scheda scelta. Home e F.A.Q. sono
  pulsanti a pillola (`nav_home`, `nav_faq`, quello aperto è `type="primary"`) che scrivono `st.session_state["scheda"]`
  (`HOME`, `FAQ` in `ui/controls_view.py`): `st.tabs` e `st.radio` non permettono altri comandi tra le pillole. Si
  disegna solo la scheda scelta. Obiettivo: la Home sta in una schermata senza scorrere (telefono 390 × 740,
  computer 1280 × 800, con lo score del petrolio): margini, distacchi (6 px), riquadro «Consiglio» e didascalie sono
  compattati per questo; controlla con Playwright prima di aggiungere spazio o elementi. In Streamlit 1.65 le colonne sono `stColumn` e il menu a tendina è un `input` dentro
  `stSelectbox`. La tabella degli archi sta in fondo a
  «F.A.Q.» (la scheda Archi è stata tolta). Indicatori della Home: prezzo medio, distributori, costo al km e, accanto, il menu del
  carburante (contenitori `metriche` e `carb`, creati in `ControlsView` solo nella Home: quattro riquadri larghi e alti uguali a ogni larghezza (da telefono
  largo le scritte stanno su una riga e gli indicatori sarebbero più bassi: `height: 100%` li allunga; le etichette in
  alto e i valori stanno alla stessa altezza di «CARBURANTE» e «Benzina», controllato con Playwright a 390, 430 e 1280 px);
  gli indicatori li scrive `ResultView` nella colonna `metriche`; nelle altre schede il menu non c'è e la scelta
  vive in `st.session_state["_carburante"]`, che non è la chiave di un widget)
  (il riquadro «Litri da fare» è stato tolto). La scheda Petrolio (pagina di scorebrent) è stata tolta: non
  rimetterla.
- **Mappa**: Leaflet con `folium` (`ui/map_leaflet.py`, niente pydeck), inserita come HTML con
  `st.iframe` (non `st.components.v1.html`, deprecato) dentro `st.container(key="mappa")`: niente `streamlit-folium`, così toccarla non fa
  ricaricare la pagina. Quadrata (`aspect-ratio: 1 / 1` sull'iframe in `style.py`), al massimo
  360 px di larghezza (360 × 360) da computer, centrata; da telefono il 90% della larghezza. Inquadratura (`fit_bounds`)
  sul percorso verso il migliore: posizione, distributore migliore e strada OSRM, zoom massimo 16, senza animazione
  (`FitBounds` con `animate: false`: prima partiva dallo zoom 10 e si avvicinava). Sfondo OpenStreetMap standard (`TILES`),
  schiarito via CSS (`SFONDO_CSS`): niente CARTO, che ora chiede una chiave e mostra «API key required». Script caricati: solo Leaflet e jQuery (i
  popup di folium lo usano). Toccando un distributore si apre il popup con il link «Portami qui» (Google Maps).
  L'HTML della mappa è in `st.cache_data` (`_mappa_html` in `ui/result_view.py`): folium cambia gli id a ogni costruzione,
  e un HTML diverso fa ricaricare l'iframe a ogni tocco; con la cache resta ferma finché i dati non cambiano.
  Fluidità: `[data-stale="true"]` resta a opacità piena (niente grigio durante i ricalcoli) e l'omino «Running» è nascosto.
  Nell'ambiente cloud i CDN e i tile sono bloccati: per provarla con Chromium servi `leaflet.js` e jQuery da npm con
  `context.route`.
- **Dati**: prezzi e anagrafica MIMIT da `ui/data_service.get_mimit_dataset`, con precedenza: CSV caricati a
  mano → cartella `data/` → copia nel branch `dati` (`fm.download_dati`, `mimit/*.csv.gz`, solo se la data di
  estrazione + 1 giorno è quella dell'ultimo aggiornamento delle 9:00: il MIMIT data i file con il giorno prima) → altrimenti la copia vecchia del branch `dati`, subito (`FONTE_VECCHIA`, «⚠️ prezzi non aggiornati» sulla riga di «CONSIGLIO», in memoria solo 15 minuti, `_RIPROVA_MIMIT`), mentre il sito MIMIT si prova in background (`controlla_mimit_in_background`: un thread alla volta, al massimo ogni 15 minuti; se risponde `_metti` sostituisce la copia; nei test `_in_background` va simulato) → solo senza copia il sito MIMIT con la pagina in attesa (`fm.download_csv`; dopo un errore il secondo file non riprova il MIMIT). Priorità alla copia `dati` decisa dall'utente: da ottobre 2026 il MIMIT blocca le connessioni dall'estero e i CSV si caricano a mano nel branch `dati`; i file scaricati
  restano in memoria fino alle 9:00 successive. La copia la salva ogni mattina `.github/workflows/aggiorna_mimit.yml`
  (`scripts/aggiorna_mimit.py`) nel branch `dati`: i CSV MIMIT non vanno mai su `main` e non si versionano.
  Brent da Yahoo Finance (`fetch_brent_yf`, cache 3 ore). `load_data` tiene al massimo 2 versioni dei CSV (`max_entries=2`, `st.cache_resource`
  senza copie, chiave corta `impronta` = lunghezza + CRC32 dei byte invece di far leggere a Streamlit 7 MB a ogni giro);
  anche `candidati` (= `build_candidates`) è in `st.cache_resource`: nessuno modifica queste tabelle (`compute_edges` copia).
  `parse_anagrafica` resta con il ciclo Python: la versione con `read_csv` è stata misurata ed è più lenta.
  `_load_data` toglie i distributori con coordinate in conflitto con il loro comune (`coordinate_sospette` in
  `ingestion/parser.py`: oltre 50 km dalla mediana del comune; con 2 soli distributori lontani più di 50 km tutti e due;
  con 1 solo oltre 200 km dalla mediana della provincia) e ne mette il numero in `anag.attrs["esclusi"]`, mostrato in
  fondo a «F.A.Q.». Anche lo storico (`storico.medie_giornaliere`, `centri_comuni`) usa il filtro.
- **OSRM**: distanze su strada per i 99 distributori più vicini (`/table` con `annotations=distance`, senza
  OSRM restituisce solo i tempi) e percorso del migliore (`/route`). Le risposte riuscite restano in memoria
  (`lru_cache`), gli errori no, ma dopo un errore OSRM non si chiama per 3 minuti (`PAUSA_DOPO_ERRORE_S`, per tutti;
  le risposte già in memoria valgono comunque, `InPausa`; nei test `osrm.riprendi()`); se OSRM non risponde (attesa massima 2,5 s per `/table`, 1,5 s per `/route`) si usa
  la linea d'aria × fattore strada.
- **Storico**: `storico.py` + `scripts/raccogli_storico.py`, lanciati ogni mattina da
  `.github/workflows/storico.yml` (CSV del giorno dalla copia `mimit/` del branch `dati`, `--mimit`; il sito MIMIT solo se manca), che salva `storico/medie_comuni.csv.gz` (mediane per comune, ultimi 40
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
- **Carburanti**: Benzina, Gasolio, GPL, Metano (`FUELS`). Per GPL e Metano (`SENZA_SELF`) la scelta Self/Servito
  non conta (quasi tutti li vendono solo serviti): `build_candidates` tiene self e servito e, per distributore, il
  prezzo più basso; il radio è disattivato. Il Metano è in kg (`fm.unita`: «kg» / «l»), e l'unità passa a
  `ResultView`, `EdgesView` e alla mappa. Serbatoio e consumo predefiniti per carburante: `PREDEFINITI` in
  `ui/controls_view.py` (widget con chiave per carburante). L-GNC e GNL non sono inclusi.
- **Calcolo** (`compute_edges`): tutto rispetto al distributore più vicino (`info["vicino"]`, prezzo `p_rif`):
  risparmio sul prezzo = litri × (`p_rif` − prezzo), km in più = 2 × (distanza − distanza del più vicino), costo del
  tempo = 2 × (minuti − minuti del più vicino) / 60 × `valore_tempo` (€/ora, 10 di default; minuti da OSRM
  `get_osrm_minuti`, stessa richiesta `/table` con `annotations=distance,duration`, o distanza a `VELOCITA_MEDIA_KMH`).
  `score` = risparmio sul prezzo + effetto Brent − costo del viaggio − costo del tempo: decide classifica e verdetto.
  `risparmio` = lo stesso senza l'effetto Brent: è quello mostrato nella frase, sulla mappa e nel Top 5
  (l'effetto Brent è uguale per tutti e non è un risparmio vero). Il prezzo di mercato (mediana o media nel raggio)
  resta per costo al km, effetto Brent, indicatore e filtro dei prezzi troppo bassi (`sconto_max`). Esclusi i
  distributori «Autostradale» (`autostrade=False`, opzione in «Opzioni»); età massima del prezzo predefinita 5 giorni. Costo al km = consumo × prezzo di mercato +
  usura. Il test `test_compute_edges_conti_a_mano` rifà i conti a mano: aggiornalo se cambi la formula.
- **Avvio**: finché `st.session_state["avviato"]` non è vero, `app.py` mostra solo `style.avvio()` (contenitore
  `avvio`, lo stesso riquadro del cerchio di caricamento con il pulsante `avvia`: cerchio verde `VERDE` con l'icona `:material/local_gas_station:`, 132 px, 114 da telefono; riquadro largo 384 px, 312 da telefono) e si ferma: niente download né
  richiesta di posizione prima del tocco. Sotto il pulsante il menu `carburante_avvio`: al tocco `_avvia` lo copia in
  `st.session_state["_carburante"]`, da cui il menu della Home prende `index`. Negli AppTest imposta `at.session_state["avviato"] = True` prima di `run()`.
- **Caricamento**: un solo cerchio al centro dello schermo (`style.Caricamento`, sopra la pagina con
  `position: fixed`) per dati MIMIT (0–60%), lettura dei CSV, Brent, score del petrolio, posizione (95%, resta finché
  il browser risponde) e distanze su strada (98%, in `app.py` prima di `compute_edges`); si chiude in fondo ad `app.py`,
  a pagina completa (prima, mentre rispondeva OSRM, la pagina si vedeva a metà). Finché la Home non è mai stata
  mostrata (`st.session_state["pronta"]`) compare subito; nei ricalcoli dopo (anche
  «Posizione», mentre il GPS risponde) compare solo oltre 0,3 s (`x-ritardo`), tranne quando la pagina si ferma a metà
  (posizione in attesa: `mostra(..., subito=True)` prima di `st.stop`). Lo sfondo è sempre pieno (`BG`): dietro
  non si vede la pagina a metà. Lo controllano `test_posizione_in_attesa_copre_la_pagina` e
  `test_cerchio_sempre_su_sfondo_pieno` in `tests/test_app.py`. Le cache hanno `show_spinner=False`. Lo score del
  petrolio si legge in `ControlsView` (`bs`, `bs_err`).
- **Posizione**: `rileva_posizione()` in cima ad `app.py`, prima della schermata d'avvio e sempre nello stesso punto
  (così la richiesta parte all'apertura e non riparte dopo il tocco). Prima il GPS (`posizione_browser`: `getLocation()`
  di streamlit_js_eval con un tempo massimo di 15 s, `GPS_ATTESA_S`, oltre il quale vale come errore); solo se fallisce
  (negato, spento, tempo scaduto) `posizione_ip` chiede al browser la posizione dall'IP (`get.geojs.io`, poi
  `ipwho.is`, 4 secondi; una volta per sessione in `st.session_state["pos_ip"]`); fuori dall'Italia o in errore Roma
  (`ROMA`). Mentre il GPS non ha risposto, dopo il tocco resta il cerchio «Cerco la tua posizione…».
  La nota «📍 Perugia (stima)» / «📍 Roma (ripiego)» sta sulla riga di «CONSIGLIO» (`kicker_html`), per non
  allungare la pagina. Nei test AppTest va simulato anche `streamlit_js_eval.streamlit_js_eval`.
- **Preferenze** (`ui/preferenze.py`): carburante e opzioni restano nel `localStorage` del browser (`refillo_opzioni`,
  JSON). `leggi()` in cima ad `app.py` (già nella schermata d'avvio) li mette in `st.session_state["_preferenze"]`
  dopo `valida()` (solo chiavi note, tipo e intervallo dei widget); `salva()` in fondo ad `app.py`, solo dopo averli
  letti, li riscrive con un `streamlit_js_eval` la cui chiave cambia solo quando cambiano. I widget di «Opzioni» hanno
  chiavi `opt_*` (più `v_tot_<carburante>` e `consumo_<carburante>`) e prendono il valore iniziale da
  `valore(chiave, predefinito)` come `value=`/`index=`: non scrivere le loro chiavi nella sessione prima di crearli,
  perché i widget dentro il popover partirebbero dal minimo. Unica eccezione `carburante_avvio`, impostato da
  `leggi()` perché il menu d'avvio esiste già quando arriva la risposta. Non si salvano livello e litri da fare.
  Negli AppTest `streamlit_js_eval` finto risponde `None` alla chiave `opzioni_leggi`: niente preferenze.
- **App installabile**: Streamlit Cloud non permette un manifest, quindi `docs/` (GitHub Pages da `main`, `/docs`,
  https://saveriopititto-bot.github.io/refillo/) ha manifest, icone (`icona.svg` → PNG) e `sw.js`, e mostra l'app a tutto
  schermo in un iframe (`?embed=true&app=1`, `allow="geolocation"`). Nell'app, `style.invito_installa()` (contenitore
  `installa`, fisso in fondo, solo sotto i 640 px, solo nella Home) porta lì; non compare con `app=1` né dopo la ×
  (`installa_chiuso` nelle preferenze) né prima che le preferenze siano lette (`opzioni_lette`).
- **Sveglia**: `.github/workflows/sveglia.yml` ogni 6 ore lancia `scripts/sveglia.py` (Playwright): apre
  refillo.streamlit.app, tocca «Yes, get this app back up!» se l'app dorme, poi il pulsante d'avvio (`.st-key-avvia
  button:visible`: c'è anche un pulsante nascosto del suggerimento) e aspetta la Home. Non scrive nel repository.
- **Riserva**: sotto la soglia di riserva il «Consiglio» dice sempre «Rifornisci», anche se lo score del
  petrolio dice altro (`info["riserva"]`).
- La logica del modello sta in `core/`, `ingestion/` e `clients/` (riesportati da `fuel_model.py`, che i test e
  l'app importano come `fm`); l'interfaccia sta in `app.py` (solo coordinamento) e nelle viste di `ui/`.
