"""Vista della scheda «Risultato»: metriche, mappa e tabella dei 5 distributori migliori."""
from __future__ import annotations

from dataclasses import dataclass
from html import escape

import pandas as pd
import streamlit as st

import style
from ui.formatters import _it, eur, num
from ui.map_deck import build_fuel_deck


@dataclass
class ResultView:
    edges: pd.DataFrame
    info: dict
    origin: tuple[float, float]
    raggio: int | float
    litri: float | None
    ref_mode: str
    show_all_lines: bool
    fonte: str

    def render(self) -> None:
        if self.edges.empty:
            style.error_card("Nessun distributore da mostrare: nessun distributore nel raggio scelto.")
            return

        best = self.info["best"]
        prezzo_txt = _it(f"{best.prezzo:.3f}") + " €/l"

        style.metrics([
            ("Prezzo di mercato", _it(f"{self.info['p_market']:.3f}") + " €/l",
             f"{self.ref_mode} nel raggio"),
            ("Distributori", str(self.info["n"]), f"nel raggio di {self.raggio} km"),
            ("Litri da fare", num(self.info["q"]) + " l", "pieno" if self.litri is None else "impostati a mano"),
            ("Costo al km", _it(f"{self.info['c_km']:.3f}") + " €/km", "carburante + usura"),
        ])

        with style.card("map"):
            style.title("Dove conviene andare")
            style.lead(
                f"Il distributore migliore è <strong>{escape(best.bandiera or best.nome)}</strong> "
                f"({escape(best.indirizzo)}, {escape(best.comune)}): <strong>{prezzo_txt}</strong> a "
                f"<strong>{num(best.dist_km)} km</strong>. Facendo il pieno lì risparmi "
                f"<strong>{eur(best.risparmio, sign=True)}</strong> rispetto al prezzo medio della zona, "
                f"considerando il costo del viaggio."
            )
            st.caption("Più un distributore è verde, più conviene")
            deck = build_fuel_deck(
                self.origin, self.edges,
                best_route=self.info.get("best_route"),
                show_all_lines=self.show_all_lines,
                raggio=self.raggio,
            )
            st.pydeck_chart(deck, height=480)
            st.caption(self.fonte)

        with style.card("top"):
            style.title("I 5 migliori")
            style.table(
                ["Distributore", "Comune", "Prezzo", "Distanza", "Risparmio"],
                [[escape(r.bandiera or r.nome or "Distributore"), escape(r.comune),
                  _it(f"{r.prezzo:.3f}") + " €/l", num(r.dist_km) + " km", eur(r.risparmio, sign=True)]
                 for _, r in self.edges.head(5).iterrows()],
            )
