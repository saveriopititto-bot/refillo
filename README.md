# ⛽ Score di rifornimento

[![Apri l'app su Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://fuelmode.streamlit.app/)
[![Test](https://github.com/saveriopititto-bot/test3/actions/workflows/tests.yml/badge.svg)](https://github.com/saveriopititto-bot/test3/actions/workflows/tests.yml)

**App online: https://fuelmode.streamlit.app/**

App Streamlit che, partendo dalla tua posizione, assegna un punteggio ai distributori vicini usando i prezzi
ufficiali del MIMIT e ti dice dove, e se, conviene fare rifornimento.

## Cosa fa

- **Usa la tua posizione reale**: il browser chiede il permesso e l'app parte dalle coordinate del dispositivo.
  In alternativa puoi scegliere un comune o inserire le coordinate a mano.
- **Usa dati sempre aggiornati**: all'apertura scarica da sola anagrafica e prezzi dal sito del MIMIT,
  senza file da caricare.
- **Dice se conviene**: confronta il prezzo di ogni distributore con il prezzo tipico della zona e toglie il
  costo dei chilometri in più. Il consiglio segue lo score del petrolio («Conviene», «Rifornisci» o
  «Aspetta»); se lo score non è disponibile, il verdetto è «Rifornisci» o «Non conviene».
- **Mostra dove andare**: una mappa con i distributori colorati dal più conveniente (verde-azzurro) al meno
  conveniente (arancione), e la classifica dei 5 migliori.
- **Considera il Brent**: scarica da solo da Yahoo Finance la variazione del petrolio (in euro) negli ultimi
  7 giorni, che anticipa se i prezzi alla pompa stanno per salire o scendere.
- **Dice dove va il petrolio**: legge da Supabase lo score del Brent calcolato ogni giorno dall'app «Prezzo
  del petrolio» ([scorebrent](https://github.com/saveriopititto-bot/scorebrent)) e lo mostra nel riquadro
  «Consiglio» in cima: «Conviene», «Rifornisci» o «Aspetta».
- **Esporta i dati**: la tabella completa degli archi posizione → distributore si scarica in CSV, per usarla
  come grafo pesato.
- **Funziona anche da telefono**: la barra laterale si apre sopra la pagina e gli indicatori si adattano
  alla larghezza dello schermo.
- **Parla italiano semplice**: niente simboli né formule nell'interfaccia; percentuali e cifre in euro, con
  i numeri in formato italiano.

Carburanti: Benzina, Gasolio, GPL e Metano, self o servito.

## Come si usa

La barra laterale è compatta e divisa in due sezioni:

1. **Dove sei**: «La mia posizione» (predefinita), «Comune» o «Coordinate».
2. **Carburante**: prodotto, capacità del serbatoio, carburante nel serbatoio (in %), consumo e raggio di
   ricerca.

In «Opzioni avanzate» ci sono self o servito (predefinito: self), i parametri del modello (soglia di riserva,
litri da fare, usura dell'auto, età massima del prezzo, strada in più rispetto alla linea d'aria, prezzo
tipico della zona, soglia di convenienza e peso del petrolio sui prezzi) e, in fondo, il blocco **Dati**: caricamento dei CSV a mano e il pulsante
«Riscarica ora», che aggiorna prezzi e Brent.

L'interfaccia usa solo nomi in italiano; i simboli della formula sono nella sezione «Il modello» qui sotto:

| Nell'app | Nella formula |
|---|---|
| Risparmio netto (tabella Archi) / Risparmio migliore | S_i / S_max |
| Risparmio (frase, mappa, 5 migliori) | S_i senza il termine Brent: q·(P_market − P_i) − D_i·C_km |
| Litri da fare | q |
| Prezzo tipico della zona | P_market |
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
| Consumo | 6,5 l/100 km |
| Raggio d'azione | 15 km su strada |
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
i casi e compatto anche da telefono. Segue lo score del petrolio, con a destra un cerchio colorato, grande
quanto il riquadro (più piccolo da telefono):

| Score | Consiglio | Frase sotto, in bianco | Cerchio |
|---|---|---|---|
| +1 | Conviene | I prezzi sono migliori della media degli ultimi trenta giorni | verde, freccia in su |
| 0 | Rifornisci | Quando ti serve | arancione, pallino |
| −1 | Aspetta | A meno che tu non ne possa fare a meno | rosso, freccia in giù |

Se lo score del petrolio non è disponibile, il riquadro torna come prima: verdetto «Rifornisci» o «Non
conviene» in base al risparmio, data dei prezzi MIMIT usati, variazione del Brent e motivo del verdetto
(il risparmio migliore rispetto alla soglia di convenienza), più una riga che dice perché lo score manca.
Lo stesso verdetto compare anche quando il serbatoio è sotto la soglia di riserva: in quel caso il riquadro dice
sempre «Rifornisci», qualunque sia lo score del petrolio.

Sotto il riquadro, le pillole delle tre schede. L'app disegna solo quella aperta: la mappa e la tabella degli
archi partono quando si apre la loro scheda, così l'avvio è più leggero.

- **Risultato**:
  - quattro indicatori compatti su una riga (prezzo di mercato, distributori nel raggio, litri da fare, costo
    al km), che restano su una riga anche da telefono;
  - il riquadro «Dove conviene andare»: subito sotto il titolo il riepilogo in una frase (insegna e indirizzo
    del distributore migliore, prezzo, distanza e risparmio reale, cioè prezzo meno viaggio, senza l'effetto
    Brent), poi la mappa, sempre in verticale (larga 2, alta 3) e al massimo larga 500 px, centrata;
  - i 5 distributori migliori, con il nome dell'impianto per distinguere quelli della stessa
    insegna.
- **Archi**: la tabella completa ed export CSV. Per ogni distributore: prezzo, distanza, km in più, risparmio
  sul prezzo, effetto Brent, costo del viaggio, risparmio netto, peso dell'arco (anche nella versione mai
  negativa), convenienza del prezzo ed età del prezzo. Le intestazioni del CSV sono le stesse della tabella.
- **Come funziona**: la spiegazione a parole, senza formule (la formula è qui sotto, in «Il modello»).

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
nei 5 migliori è S_i senza il termine Brent, che è uguale per tutti e non è un risparmio vero: sposta solo il
verdetto. La classifica non cambia. Il peso di ogni arco è `−S_i` (per il cammino minimo) oppure `S_max − S_i` se servono pesi non
negativi.

## Dati

L'app usa gli open data MIMIT `anagrafica_impianti_attivi.csv` e `prezzo_alle_8.csv`. Li prende da, in
ordine:

1. i file caricati a mano da «Opzioni avanzate» → «Dati» nella barra laterale;
2. i file nella cartella `data/` (vedi `data/README.md`), utile offline o per analizzare un giorno preciso;
3. il download dal sito del MIMIT, tenuto in cache per 3 ore perché i prezzi cambiano una volta al giorno.

I CSV letti restano in memoria (al massimo le ultime due versioni, per non riempire la memoria del server
con i giorni vecchi).

Se il download non riesce, l'app lo dice e propone di caricare i file a mano. Data dei prezzi e ora del
download compaiono nel riquadro della decisione.

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
«Aggiorna posizione» la rileva di nuovo.

Se il permesso viene negato, l'app spiega come riattivarlo dalle impostazioni del sito nel browser e propone
Comune o Coordinate.

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

| File | Contenuto |
|---|---|
| `app.py` | Interfaccia Streamlit: barra laterale, schede Risultato, Archi e Come funziona, geolocalizzazione |
| `fuel_model.py` | Download e lettura dei CSV MIMIT, geometria, Brent da Yahoo Finance, score del Brent da Supabase, calcolo degli score |
| `style.py` | Stile dell'interfaccia: CSS, schede arrotondate e blocchi HTML |
| `.streamlit/config.toml` | Tema: palette e angoli arrotondati |
| `data/` | Cartella opzionale per i CSV MIMIT (non versionati) |
| `storico.py` | Storico dei prezzi: mediane giornaliere per comune, centri dei comuni, lettura degli archivi trimestrali MIMIT |
| `scripts/raccogli_storico.py` | Script che aggiorna lo storico (prezzi di oggi o archivi trimestrali) |
| `tests/test_fuel_model.py` | Test di parsing, filtri, download, Brent, score del Brent da Supabase e score |
| `tests/test_storico.py` | Test dello storico: mediane, finestra di 40 giorni, archivi, lettura e scrittura |
| `.github/workflows/tests.yml` | CI con GitHub Actions |
| `.github/workflows/storico.yml` | Azione giornaliera che aggiorna lo storico nel branch `dati` |
| `CLAUDE.md` | Istruzioni per Claude Code: flusso di lavoro (PR e merge automatici), controlli, convenzioni |

Lo stile è lo stesso di test4 (layout «1a»: riquadro «Consiglio» in cima e sotto la navigazione a pillole, senza titolo, schede bianche arrotondate, palette
`#8ecae6` `#219ebc` `#023047` `#ffb703` `#fb8500`, font Archivo). I selettori CSS si agganciano ad attributi
interni di Streamlit, testati con la 1.65: se dopo un aggiornamento un elemento perde lo stile, va aggiornato
il selettore.
