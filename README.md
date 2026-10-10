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
  costo dei chilometri in più. Il verdetto è «Rifornisci» o «Non conviene».
- **Mostra dove andare**: una mappa con i distributori colorati dal più conveniente (verde-azzurro) al meno
  conveniente (arancione), e la classifica dei 5 migliori.
- **Considera il Brent**: scarica da solo da Yahoo Finance la variazione del petrolio (in euro) negli ultimi
  7 giorni, che anticipa se i prezzi alla pompa stanno per salire o scendere.
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
| Risparmio netto / Risparmio migliore | S_i / S_max |
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

Il risultato è diviso in tre schede:

- **Risultato**:
  - il riepilogo in una frase: insegna e indirizzo del distributore migliore, prezzo, distanza e risparmio;
  - il riquadro della decisione, compatto: verdetto, motivo, data dei prezzi MIMIT usati e variazione del
    Brent, in poco spazio anche da telefono;
  - quattro indicatori compatti su una riga (prezzo di mercato, distributori nel raggio, litri da fare, costo
    al km), che restano su una riga anche da telefono;
  - la mappa e i 5 distributori migliori, con il nome dell'impianto per distinguere quelli della stessa
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
- **D_i**: chilometri in più, cioè andata e ritorno dalla tua posizione al distributore. Le distanze sono in
  linea d'aria per un fattore strada (1,3 di default). Il modello in `fuel_model.compute_edges` gestisce anche
  una destinazione (conta solo la deviazione dal percorso), ma l'app non la usa.
- **C_km**: costo al km, cioè consumo × P_market + usura.

Si rifornisce se il punteggio migliore supera la soglia θ, oppure se il serbatoio è sotto la soglia di
riserva L_min. Il peso di ogni arco è `−S_i` (per il cammino minimo) oppure `S_max − S_i` se servono pesi non
negativi.

## Dati

L'app usa gli open data MIMIT `anagrafica_impianti_attivi.csv` e `prezzo_alle_8.csv`. Li prende da, in
ordine:

1. i file caricati a mano da «Opzioni avanzate» → «Dati» nella barra laterale;
2. i file nella cartella `data/` (vedi `data/README.md`), utile offline o per analizzare un giorno preciso;
3. il download dal sito del MIMIT, tenuto in cache per 3 ore perché i prezzi cambiano una volta al giorno.

Se il download non riesce, l'app lo dice e propone di caricare i file a mano. Data dei prezzi e ora del
download compaiono nel riquadro della decisione.

Il Brent e il cambio EUR/USD arrivano da Yahoo Finance (`yfinance`), anche loro con una cache di 3 ore. Se
Yahoo non risponde, l'app lo segnala e usa ΔB = 0, cioè ignora il termine Brent.

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
| `fuel_model.py` | Download e lettura dei CSV MIMIT, geometria, Brent da Yahoo Finance, calcolo degli score |
| `style.py` | Stile dell'interfaccia: CSS, schede arrotondate e blocchi HTML |
| `.streamlit/config.toml` | Tema: palette e angoli arrotondati |
| `data/` | Cartella opzionale per i CSV MIMIT (non versionati) |
| `tests/test_fuel_model.py` | Test di parsing, filtri, download, Brent e score |
| `.github/workflows/tests.yml` | CI con GitHub Actions |
| `CLAUDE.md` | Istruzioni per Claude Code: flusso di lavoro (PR e merge automatici), controlli, convenzioni |

Lo stile è lo stesso di test4 (layout «1a»: navigazione a pillole, schede bianche arrotondate, palette
`#8ecae6` `#219ebc` `#023047` `#ffb703` `#fb8500`, font Archivo). I selettori CSS si agganciano ad attributi
interni di Streamlit, testati con la 1.65: se dopo un aggiornamento un elemento perde lo stile, va aggiornato
il selettore.
