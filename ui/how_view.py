"""Vista della scheda «Come funziona»: guida descrittiva sul modello e sulle fonti dati."""
from __future__ import annotations

from dataclasses import dataclass

import streamlit as st

import style


@dataclass
class HowView:
    fonte: str

    def render(self) -> None:
        with style.card("how"):
            style.title("Come funziona")
            st.markdown(
                """
L'app guarda i distributori intorno a te e stima, per ciascuno, **quanto risparmi facendo lì il rifornimento**.

- **Il prezzo**: confronta il prezzo di ogni distributore con quello tipico della zona e calcola quanto spendi
  in meno (o in più) per i litri che devi fare.
- **Il viaggio**: toglie quanto ti costa arrivarci e tornare, cioè carburante e usura dell'auto per i
  chilometri di andata e ritorno.
- **Il petrolio**: se negli ultimi giorni il Brent è salito, i prezzi alla pompa tenderanno a salire e fare
  rifornimento ora conviene un po' di più; se è sceso, conviene un po' meno. Questo vale per tutti i
  distributori allo stesso modo, quindi cambia il verdetto ma non la classifica.

Il risultato è un punteggio in euro: più è alto, più conviene. Il verdetto è **Rifornisci** se il distributore
migliore fa risparmiare (oltre la soglia scelta in «Opzioni»), oppure se il serbatoio è quasi vuoto.

I prezzi e i distributori sono quelli ufficiali del MIMIT, aggiornati ogni giorno; il Brent arriva da Yahoo
Finance. Le distanze sono quelle su strada calcolate dal servizio OSRM; se non risponde, sono stimate in linea
d'aria, corrette per tenere conto delle strade.
"""
            )
            st.caption(self.fonte)
