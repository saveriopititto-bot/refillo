# Dati

Metti qui i due CSV open data MIMIT (https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti):

- `anagrafica_impianti_attivi.csv`
- `prezzo_alle_8.csv`

Non è obbligatorio: se la cartella è vuota l'app scarica da sola i file aggiornati (dal branch `dati` o dal sito del MIMIT).
I file messi qui hanno la precedenza sul download (utile offline o per analizzare un giorno preciso);
quelli caricati a mano da «Opzioni avanzate» hanno la precedenza su tutto.
I CSV non sono versionati (vedi `.gitignore`).
