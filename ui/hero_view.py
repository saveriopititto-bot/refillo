"""Componente per il riquadro in evidenza «Consiglio» in cima alla pagina."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Sequence

import pandas as pd

import fuel_model as fm
import style
from ui.data_service import NOTA_PRECISA, nota_score, perche_petrolio
from ui.formatters import _it


@dataclass
class HeroView:
    container: any  # colonna del testo nel riquadro «Consiglio»
    cerchio: any  # posto del cerchio dello score, sopra il menu del carburante
    edges: pd.DataFrame
    info: dict
    bs: dict | None
    bs_err: str
    note_dati: Sequence[str]
    nota_posizione: str = ""  # posizione approssimativa (dall'indirizzo internet o Roma)

    def render(self) -> None:
        with self.container:
            self._render()

    def _pos(self) -> str:
        """« · 📍 Perugia (stima)» da mettere sulla riga di «CONSIGLIO», con la spiegazione al passaggio del mouse."""
        if not self.nota_posizione:
            return ""
        return f' · <span class="x-pos" title="{escape(NOTA_PRECISA)}">📍 {escape(self.nota_posizione)}</span>'

    def _render(self) -> None:
        if self.edges.empty:
            style.error_card("Nessun distributore nel raggio scelto con un prezzo valido. "
                             "Aumenta il raggio o l'età massima del prezzo.")
            style.html(f'<p class="x-note">{"<br>".join(self.note_dati)}{self._pos()}</p>')
        elif self.bs is not None and not self.info["riserva"]:
            titolo = fm.BRENT_SCORE_TESTI[self.bs["esito"]]
            style.hero("Consiglio", titolo, "", "", nota_html=perche_petrolio(self.bs), kicker_html=self._pos())
            with self.cerchio:
                style.html('<div class="x-hero-aside">'
                           + style.cerchio_score(self.bs["esito"], "Petrolio: " + titolo) + "</div>")
        else:
            corpo = escape(_it(self.info["motivo"][0].upper() + self.info["motivo"][1:])) + "."
            if not self.info["consiglio"]:
                corpo += " Il termine Brent è uguale per tutti i distributori: sposta lo score ma non cambia la classifica."
            meta = list(self.note_dati) + ([nota_score(self.bs_err)] if self.bs is None else [])
            style.hero("Consiglio", "Rifornisci" if self.info["consiglio"] else "Non conviene",
                       "", corpo, meta_html=meta, kicker_html=self._pos())


def render_error(container: any, msg: str) -> None:
    with container:
        style.error_card(msg)
