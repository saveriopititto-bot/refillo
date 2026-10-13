"""Testo della scheda «F.A.Q.»: come funziona il calcolo, da dove vengono i dati, privacy."""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

import style


@dataclass
class HowView:
    fonte: str
    esclusi: int = 0  # distributori tolti perché le coordinate non tornano con il loro comune

    def render(self) -> None:
        with style.card("how"):
            style.title("Come funziona")
            st.markdown(
                """
L'app guarda i distributori intorno a te e stima, per ciascuno, **quanto risparmi facendo lì il rifornimento**.

- **Il prezzo**: confronta il prezzo di ogni distributore con quello del distributore più vicino a te (come fare
  benzina sotto casa) e calcola quanto spendi in meno (o in più) per i litri che devi fare.
- **Il viaggio**: toglie quanto ti costano i chilometri in più, andata e ritorno, rispetto al più vicino:
  carburante, usura dell'auto e il tuo tempo (10 € all'ora di default, si cambia in «Opzioni»).
- **Esclusi**: i distributori in autostrada (si possono includere in «Opzioni») e i prezzi comunicati da più di
  5 giorni.
- **Il petrolio**: se negli ultimi giorni il Brent è salito, i prezzi alla pompa tenderanno a salire e fare
  rifornimento ora conviene un po' di più; se è sceso, conviene un po' meno. Questo vale per tutti i
  distributori allo stesso modo, quindi cambia il verdetto ma non la classifica.

Il risultato è un punteggio in euro: più è alto, più conviene. Il verdetto è **Rifornisci** se il distributore
migliore fa risparmiare (oltre la soglia scelta in «Opzioni»), oppure se il serbatoio è quasi vuoto.

I prezzi e i distributori sono quelli ufficiali del MIMIT; il Brent arriva da Yahoo Finance. Le distanze sono
quelle su strada calcolate dal servizio OSRM; se non risponde, sono stimate in linea d'aria, corrette per tenere
conto delle strade.

**Il consiglio in cima funziona?** L'abbiamo provato sui prezzi medi italiani dal 2015 a oggi. Quando diceva
«Conviene», nella settimana dopo benzina e gasolio sono saliti più di 9 volte su 10; quando diceva «Aspetta»,
sono scesi più di 9 volte su 10. Seguirlo ha fatto risparmiare in media tra 60 centesimi e 1 € a pieno (50 litri).
«Conviene» e «Aspetta» sono rari: quasi sempre dice «Rifornisci», perché il petrolio non spinge i prezzi né in su né in giù.

**Quanto sono aggiornati i prezzi.** Il MIMIT pubblica l'elenco una volta al giorno, la mattina, con i prezzi
comunicati dai gestori fino alle 8. Se un distributore cambia prezzo durante la giornata, l'app lo vede solo il
giorno dopo: alla pompa vale sempre il prezzo esposto.

**I tuoi dati.** Niente account e niente pubblicità.
- La posizione serve solo a trovare i distributori vicini: l'app la usa per il calcolo e non la registra.
- Le distanze su strada si chiedono al servizio OSRM, mandandogli le coordinate della tua posizione e dei
  distributori.
- Se il GPS non risponde, il browser chiede una posizione approssimativa a due servizi esterni (geojs.io e
  ipwho.is), che per rispondere vedono il tuo indirizzo internet.
- Le opzioni scelte restano solo nel tuo browser: cancellando i dati del sito tornano quelle di partenza.
- «Portami qui» apre Google Maps. L'app è ospitata da Streamlit Community Cloud, che ha le sue regole sulla privacy.
"""
            )
            nota = self.fonte
            if self.esclusi:
                nota += (f" · {self.esclusi} distributori esclusi perché nei dati MIMIT le coordinate non tornano con "
                         "il loro comune (per esempio un distributore di Finale Emilia nel centro di Milano)")
            st.caption(nota)
