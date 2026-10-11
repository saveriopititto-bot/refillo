# ⛽ Score di rifornimento

[![Apri l'app su Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://refillo.streamlit.app/)
[![Test](https://github.com/saveriopititto-bot/refillo/actions/workflows/tests.yml/badge.svg)](https://github.com/saveriopititto-bot/refillo/actions/workflows/tests.yml)

**App online: https://refillo.streamlit.app/**

App Streamlit che, partendo dalla tua posizione, assegna un punteggio ai distributori vicini usando i prezzi
ufficiali del MIMIT e ti dice dove, e se, conviene fare rifornimento.

## Cosa fa

- **Usa la tua posizione reale**: il browser chiede il permesso e l'app parte dalle coordinate del dispositivo.
  In alternativa puoi scegliere un comune.
- **Usa dati sempre aggiornati**: all'apertura scarica da sola anagrafica e prezzi dal sito del MIMIT,
  senza file da caricare.
- **Dice se conviene**: confronta il prezzo di ogni distributore con il prezzo tipico della zona e toglie il
  costo dei chilometri in più. Il consiglio segue lo score del petrolio («Conviene», «Rifornisci» o
  «Aspetta»); se lo score non è disponibile, il verdetto è «Rifornisci» o «Non conviene».
- **Mostra dove andare**: una mappa (Leaflet) con i distributori colorati dal più conveniente (verde-azzurro) al
  meno conveniente (arancione), e la classifica «Top 5». Toccando un distributore si apre un riquadro con
  prezzo, distanza, risparmio e il link «Portami qui», che apre il percorso nel navigatore (Google Maps).
- **Considera il Brent**: scarica da solo da Yahoo Finance la variazione del petrolio (in euro) negli ultimi
  7 giorni, che anticipa se i prezzi alla pompa stanno per salire o scendere.
- **Dice dove va il petrolio**: legge da Supabase lo score del Brent calcolato ogni giorno dall'app «Prezzo
  del petrolio» ([scorebrent](https://github.com/saveriopititto-bot/scorebrent)) e lo mostra nel riquadro
  «Consiglio» in cima: «Conviene», «Rifornisci» o «Aspetta».
- **Esporta i dati**: la tabella completa degli archi posizione → distributore si scarica in CSV, per usarla
  come grafo pesato.
- **Funziona anche da telefono**: l'interfaccia si sviluppa in modo lineare su una sola colonna senza menu a comparsa e gli indicatori si adattano alla larghezza dello schermo.
- **Parla italiano semplice**: niente simboli né formule nell'interfaccia; percentuali e cifre in euro, con
  i numeri in formato italiano.

Carburanti: Benzina e Gasolio (self o servito), GPL e Metano. GPL e Metano si vendono quasi sempre solo serviti
(in self li hanno pochissimi distributori), quindi per loro la scelta self/servito non conta: si usa il prezzo
che c'è e, se un distributore li ha entrambi, il più basso. Il Metano si paga a chilo: prezzi in €/kg, serbatoio in
kg e consumo in kg/100 km. Serbatoio e consumo predefiniti cambiano con il carburante (si possono modificare in
«Opzioni»):

| Carburante | Serbatoio | Consumo |
|---|---|---|
| Benzina, Gasolio | 50 l | 5 l/100 km |
| GPL | 40 l | 7 l/100 km |
| Metano | 14 kg | 4 kg/100 km |

## Come si usa

- **Carburante**: il menu (Benzina, Gasolio, GPL, Metano) sta nel riquadro «Consiglio», a destra, sotto il
  cerchio dello score.
- **Dove sei**: la posizione arriva dal browser; «Posizione» la rileva di nuovo. In alternativa si sceglie
  un comune in «Opzioni».
- La riga in cima al riquadro delle schede, sempre su una riga anche da telefono: «Home», «Posizione»,
  «Opzioni», «Top 5» e «F.A.Q.», cinque pillole della stessa larghezza che riempiono tutta la riga, con lo stesso
  sfondo tenue e il testo normale. «Opzioni» e «Top 5» si aprono come popover, cioè un riquadro sopra la pagina
  che si chiude toccando fuori; «Opzioni» resta aperto mentre si cambiano i valori. «Top 5» mostra i 5
  distributori che convengono di più (insegna, comune, prezzo, distanza, risparmio; da telefono senza il comune).

In «Opzioni» ci sono i parametri del veicolo e del modello (capacità del serbatoio, livello attuale,
consumo, raggio d'azione, OSRM per percorsi reali, self o servito, soglia di riserva, litri da fare, usura dell'auto, età massima
del prezzo, fattore strada, prezzo tipico della zona, soglia di convenienza e peso del petrolio sui prezzi) e,
in fondo, il blocco **Dati**: caricamento dei CSV a mano e il pulsante «Riscarica ora», che aggiorna prezzi e Brent.
A piè di pagina in tutte le schede è presente il colofon con versione e diritti riservati.

L'interfaccia usa solo nomi in italiano; i simboli della formula sono nella sezione «Il modello» qui sotto:

| Nell'app | Nella formula |
|---|---|
| Risparmio netto (tabella degli archi) / Risparmio migliore | S_i / S_max |
| Risparmio (frase, mappa, Top 5) | S_i senza il termine Brent: q·(P_market − P_i) − D_i·C_km |
| Litri da fare | q |
| Prezzo medio (indicatore) / Prezzo tipico della zona (opzione) | P_market |
| Km in più | D_i |
| Costo al km | C_km |
| Soglia di convenienza | θ |
| Peso del petrolio sui prezzi | α |
| Variazione del Brent | ΔB |
| Carburante nel serbatoio / Soglia di riserva | L / L_min |
| Convenienza prezzo | E_p |

### Valori predefiniti

| Impostazione | Valore |
|---|---|
| Capacità del serbatoio | 50 l |
| Carburante nel serbatoio | 25% |
| Consumo | 5,0 l/100 km |
| Raggio d'azione | 20 km su strada |
| Soglia di riserva | 10% |
| Litri da fare | il pieno |
| Self o servito | self |
| Usura dell'auto | 0,05 €/km |
| Età massima del prezzo | 7 giorni |
| Strada in più rispetto alla linea d'aria | × 1,3 |
| Prezzo tipico della zona | mediana |
| Soglia di convenienza | 0 € |
| Peso del petrolio sui prezzi | 20% |

### Schede

In cima alla pagina, senza titolo, c'è il riquadro «Consiglio», visibile in tutte le schede: blu petrolio in tutti
i casi e compatto anche da telefono. Segue lo score del petrolio, con a destra un cerchio colorato (più piccolo
da telefono) e, sotto il cerchio, il menu del carburante:

| Score | Consiglio | Cerchio |
|---|---|---|
| +1 | Conviene | verde, freccia in su |
| 0 | Rifornisci | arancione, pallino |
| −1 | Aspetta | rosso, freccia in giù |

Sotto il consiglio, una frase spiega il perché:

- Conviene: «Il petrolio costa più del solito. Tra pochi giorni anche la benzina costerà di più. Fai benzina oggi.»
- Rifornisci: «Il petrolio costa come al solito. La benzina non cambierà molto. Fai benzina quando ti serve.»
- Aspetta: «Il petrolio costa meno del solito. Tra pochi giorni anche la benzina costerà di meno. Se puoi, aspetta.»

Se lo score del petrolio non è disponibile, il riquadro torna come prima: verdetto «Rifornisci» o «Non
conviene» in base al risparmio, data dei prezzi MIMIT usati, variazione del Brent e motivo del verdetto
(il risparmio migliore rispetto alla soglia di convenienza), più una riga che dice perché lo score manca.
Lo stesso verdetto compare anche quando il serbatoio è sotto la soglia di riserva: in quel caso il riquadro dice
sempre «Rifornisci», qualunque sia lo score del petrolio.

Sotto, un unico riquadro: in cima la riga Home · «Posizione» · «Opzioni» · «Top 5» · F.A.Q., tutta a sinistra e
sempre in linea anche da telefono, e sotto il contenuto della scheda scelta. L'app disegna solo la scheda aperta: la mappa e la tabella
degli archi partono quando si apre la loro scheda, così l'avvio è più leggero.

- **Home**:
  - tre indicatori compatti su una riga (prezzo medio, distributori nel raggio, costo al km), che restano su
    una riga anche da telefono;
  - il riquadro della mappa, senza titolo: in cima il riepilogo in una frase (insegna e indirizzo
    del distributore migliore, prezzo, distanza e risparmio reale, cioè prezzo meno viaggio, senza l'effetto
    Brent), poi la mappa Leaflet, quadrata e al massimo larga 400 px (400 × 400), centrata, inquadrata sul percorso
    dalla tua posizione al distributore migliore (gli altri restano visibili allontanando la mappa):
    sfondo OpenStreetMap schiarito, la tua posizione (pallino blu scuro), il percorso su strada verso il migliore (bordato di
    blu scuro) e, toccando un distributore, il riquadro con i dati e «Portami qui».
- **F.A.Q.**: «Come funziona», la spiegazione a parole, senza formule (la formula è qui sotto, in «Il modello»), e sotto
  la tabella completa degli archi con l'export CSV. Per ogni distributore: prezzo, distanza, km in più, risparmio
  sul prezzo, effetto Brent, costo del viaggio, risparmio netto, peso dell'arco (anche nella versione mai
  negativa), convenienza del prezzo ed età del prezzo. Le intestazioni del CSV sono le stesse della tabella.

## Il modello

$$S_i = q\,[(P_{market}-P_i) + \alpha\,P_{market}\,\Delta B] - D_i\,C_{km}$$

- **q**: litri da fare (di default il pieno, `V_tot·(1−L)`).
- **P_market**: mediana (o media) dei prezzi dei distributori nel raggio.
- **ΔB**: variazione del Brent in euro negli ultimi 7 giorni (Brent `BZ=F` diviso il cambio `EURUSD=X`, da
  Yahoo Finance), limitata a ±10%; **α** è la quota che passa ai prezzi. Il termine è uguale per tutti i
  distributori: sposta il verdetto ma non la classifica.
- **D_i**: chilometri in più, cioè andata e ritorno dalla tua posizione al distributore. Le distanze sono su
  strada, chieste al server pubblico OSRM per i 99 distributori più vicini (opzione «Calcola percorsi reali»,
  attiva di default; le risposte restano in memoria finché il server è acceso, così cambiare litri, consumo o
  soglie non rifà la richiesta). Senza OSRM, o se non risponde, sono in linea d'aria per un fattore strada
  (1,3 di default).
- **C_km**: costo al km, cioè consumo × P_market + usura.

Si rifornisce se il punteggio migliore supera la soglia θ, oppure se il serbatoio è sotto la soglia di
riserva L_min (che vale anche sopra lo score del petrolio). Il risparmio mostrato nella frase, nella mappa e
nel Top 5 è S_i senza il termine Brent, che è uguale per tutti e non è un risparmio vero: sposta solo il
verdetto. La classifica non cambia. Il peso di ogni arco è `−S_i` (per il cammino minimo) oppure `S_max − S_i` se servono pesi non
negativi.

## Dati

L'app usa gli open data MIMIT `anagrafica_impianti_attivi.csv` e `prezzo_alle_8.csv`. Li prende da, in
ordine:

1. i file caricati a mano da «Opzioni» → «Dati»;
2. i file nella cartella `data/` (vedi `data/README.md`), utile offline o per analizzare un giorno preciso;
3. la copia compressa salvata ogni mattina nel branch **`dati`** (`mimit/*.csv.gz`), se è quella dell'ultimo
   aggiornamento delle 9:00 (il MIMIT data i file con il giorno prima: quelli dell'11 mattina dicono «Estrazione
   del» 10);
4. altrimenti il download dal sito del MIMIT.

I file scaricati (dal branch `dati` o dal MIMIT) restano in memoria fino al prossimo aggiornamento delle 9:00.
La copia nel branch `dati` la prepara un'azione GitHub (`.github/workflows/aggiorna_mimit.yml`, ogni mattina
alle 7:05 UTC, script `scripts/aggiorna_mimit.py`): scaricarla da GitHub è più veloce e affidabile del sito
del ministero. L'azione non scrive mai su `main`.

I CSV letti restano in memoria (al massimo le ultime due versioni, per non riempire la memoria del server
con i giorni vecchi).

Se il download non riesce, l'app lo dice e propone di caricare i file a mano. Data dei prezzi, ora del
download e provenienza (copia GitHub del branch `dati` o sito del MIMIT) compaiono nel riquadro della decisione.

Il Brent e il cambio EUR/USD arrivano da Yahoo Finance (`yfinance`), anche loro con una cache di 3 ore. Se
Yahoo non risponde, l'app lo segnala e usa ΔB = 0, cioè ignora il termine Brent.

## Score del petrolio (da Supabase)

Lo score del Brent è calcolato dall'app «Prezzo del petrolio» (repository
[scorebrent](https://github.com/saveriopititto-bot/scorebrent)), che lo scrive ogni giorno di borsa, dopo le
22:30 UTC, nella tabella `brent_score` di Supabase. FuelMode legge da lì l'ultimo esito.

- **Conviene** (+1): il Brent è sopra la sua media degli ultimi 30 giorni più del solito. I prezzi alla pompa
  tendono a seguirlo con qualche giorno di ritardo, quindi conviene non aspettare.
- **Rifornisci** (0, quando ti serve): il Brent è vicino alla sua media; il petrolio non spinge i prezzi né in su né in giù.
- **Aspetta** (−1): il Brent è sotto la sua media più del solito, e i prezzi alla pompa tendono a scendere.

Lo stesso esito decide il riquadro «Consiglio» in cima, con il cerchio colorato: verde con freccia in su
(Conviene), arancione con pallino (Rifornisci), rosso con freccia in giù (Aspetta). Il riquadro resta sempre
blu petrolio, in tutti i casi; il cerchio è bianco dentro.

Lo score **non entra nel calcolo** del risparmio né nella classifica dei distributori, che continuano a usare
la variazione del Brent degli ultimi 7 giorni presa da Yahoo Finance: decide solo il consiglio mostrato in cima.

**Configurazione**: i segreti vanno nei Secrets **di questa app su Streamlit Cloud** (non nei secret del
repository GitHub, che servono solo all'esportazione di scorebrent). Su https://share.streamlit.io, accanto a
FuelMode, *⋮ → Settings → Secrets*, incolla e salva:

```toml
SUPABASE_URL = "https://<progetto>.supabase.co"
SUPABASE_ANON_KEY = "<chiave anon o publishable>"
```

Va usata la chiave **pubblica** (`anon` o `publishable`) del progetto, non quella `service_role`: permette
solo di leggere. In locale si possono usare le variabili d'ambiente con gli stessi nomi, oppure il file
`.streamlit/secrets.toml` (escluso da git).

I nomi non distinguono maiuscole e minuscole. Per la chiave vanno bene anche `SUPABASE_KEY` e
`SUPABASE_PUBLISHABLE_KEY`. In alternativa i due valori possono stare in una sezione che nel nome contiene
«supabase», come `[supabase]` o `[connections.supabase]`:

```toml
[supabase]
url = "https://<progetto>.supabase.co"
anon_key = "<chiave anon o publishable>"
```

Senza configurazione il riquadro «Consiglio» dice quale segreto manca ed elenca i nomi dei segreti che l'app trova (mai i
valori), per capire se sono stati salvati con un altro nome o nell'app sbagliata. Quel messaggio non resta in
memoria: appena i segreti vengono salvati, alla prossima apertura l'app li trova. Lo score letto, invece, è
tenuto in cache per 3 ore e «Riscarica ora» lo rilegge.

Se compare «non raggiungibile», il messaggio tra parentesi dice perché: per esempio `401` se la chiave è
sbagliata, «tabella vuota» se l'esportazione di scorebrent non ha ancora scritto nessuna riga.

## Storico dei prezzi

Per confrontare i prezzi di oggi con quelli delle settimane passate, un'azione GitHub
(`.github/workflows/storico.yml`) gira ogni mattina alle 7:17 UTC: scarica i CSV MIMIT del giorno e salva
nel branch **`dati`** due file:

- `storico/medie_comuni.csv.gz`: per ogni giorno, comune, carburante e self/servito, la mediana dei prezzi e
  il numero di distributori (stessi filtri dell'app: prezzi plausibili e non più vecchi di 7 giorni). Tiene
  gli ultimi 40 giorni;
- `storico/comuni.csv.gz`: il centro di ogni comune (mediana delle coordinate dei distributori), per sapere
  quali comuni cadono nel raggio.

L'azione si può avviare anche a mano da GitHub (*Actions → Storico prezzi → Run workflow*): con il campo
«archivio» vuoto salva i prezzi di oggi; con uno o più URL degli archivi trimestrali MIMIT (tar.gz) riempie
lo storico a ritroso con i giorni che il file conserva. In locale:

```bash
python scripts/raccogli_storico.py --cartella storico                  # prezzi di oggi
python scripts/raccogli_storico.py --cartella storico --archivio X.tar.gz
```

Lo storico servirà allo score «prezzi rispetto agli ultimi 30 giorni», in sviluppo su un branch separato.

## Posizione

La posizione arriva dall'API Geolocation del browser, tramite `streamlit-js-eval`. Funziona solo su HTTPS
(come su Streamlit Cloud) o su `localhost`. Su telefono usa il GPS; su computer di solito è più approssimativa,
perché il browser la stima dalla rete. Nella barra laterale compaiono coordinate e precisione, e
«Posizione» la rileva di nuovo.

Se il permesso viene negato, l'app spiega come riattivarlo dalle impostazioni del sito nel browser e propone
Comune.

## Avvio in locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Test

```bash
pip install pytest
python -m pytest
```

I test girano anche in CI con GitHub Actions, su Python 3.10 e 3.12, a ogni pull request e a ogni push su
`main`, insieme a un controllo della sintassi di tutti i file (compreso `app.py`, che i test non importano).

## Deploy

L'app è pubblicata su Streamlit Community Cloud dal branch `main` (file `app.py`, Python 3.12): ogni merge su
`main` aggiorna l'app online.

## Struttura

| File / Cartella | Contenuto |
|---|---|
| `app.py` | Coordinatore dell'interfaccia Streamlit: controlli, calcolo, riquadro consiglio e schede (le viste sono in `ui/`) |
| `fuel_model.py` | Facade pubblica e retrocompatibile del modello (riesporta core, ingestion, clients) |
| `core/` | Logica di business: tipi (`types.py`), geometria (`geo.py`), scoring e pesi degli archi (`model.py`) |
| `ingestion/` | Ingestione dati MIMIT: download (`downloader.py`) e parsing (`parser.py`) |
| `clients/` | Client per API esterne: OSRM (`osrm.py`), Yahoo Finance (`yahoo.py`), Supabase (`supabase.py`) |
| `ui/` | Moduli interfaccia: viste delle schede (`result_view`, `edges_view`, `how_view`), hero (`hero_view`), controlli (`controls_view`), dati e geolocalizzazione (`data_service`), mappa Leaflet (`map_leaflet.py`), formattatori (`formatters.py`), configurazione (`config.py`) |
| `style.py` | Stile dell'interfaccia: CSS, schede arrotondate, colofon e blocchi HTML |
| `.streamlit/config.toml` | Tema: palette e angoli arrotondati |
| `data/` | Cartella opzionale per i CSV MIMIT (non versionati) |
| `storico.py` | Storico dei prezzi: mediane giornaliere per comune, centri dei comuni, lettura degli archivi trimestrali MIMIT |
| `scripts/raccogli_storico.py` | Script che aggiorna lo storico (prezzi di oggi o archivi trimestrali) |
| `scripts/aggiorna_mimit.py` | Script che scarica i CSV MIMIT del giorno e li salva compressi (per il branch `dati`) |
| `tests/` | Suite di test: test del modello, dello storico, dei calcoli geometrici, dei formattatori e della configurazione |
| `.github/workflows/tests.yml` | CI con GitHub Actions |
| `.github/workflows/storico.yml` | Azione giornaliera che aggiorna lo storico nel branch `dati` |
| `.github/workflows/aggiorna_mimit.yml` | Azione giornaliera che salva i CSV MIMIT del giorno nel branch `dati` (`mimit/`) |
| `CLAUDE.md` | Istruzioni per Claude Code: flusso di lavoro (PR e merge automatici), controlli, convenzioni |

Lo stile è lo stesso di test4 (layout «1a»: riquadro «Consiglio» in cima e sotto la navigazione a pillole, senza titolo, schede bianche arrotondate, palette
`#8ecae6` `#219ebc` `#023047` `#ffb703` `#fb8500`, font Archivo). I selettori CSS si agganciano ad attributi
interni di Streamlit, testati con la 1.65: se dopo un aggiornamento un elemento perde lo stile, va aggiornato
il selettore.
