"""Vista della scheda «Archi»: tabella completa di tutti i distributori nel raggio con download CSV."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

import style


@dataclass
class EdgesView:
    edges: pd.DataFrame
    origin: tuple[float, float]
    unita: str = "l"  # «kg» per il Metano

    def render(self) -> None:
        if self.edges.empty:
            style.error_card("Nessun arco da mostrare: nessun distributore nel raggio scelto.")
            return

        prezzo_col = f"Prezzo (€/{self.unita})"
        tab = self.edges.rename(
            columns={
                "rank": "#", "bandiera": "Bandiera", "nome": "Impianto", "indirizzo": "Indirizzo", "comune": "Comune",
                "prezzo": prezzo_col, "dist_km": "Distanza (km)", "dev_km": "Km in più",
                "guadagno": "Risparmio sul prezzo (€)", "brent": "Effetto Brent (€)", "costo_log": "Costo del viaggio (€)",
                "score": "Risparmio netto (€)", "peso": "Peso arco", "peso_pos": "Peso arco (≥ 0)", "ep": "Convenienza prezzo",
                "ep_pct": "Convenienza prezzo (posizione)", "eta_giorni": "Età prezzo (gg)",
            }
        )
        cols = ["#", "Bandiera", "Impianto", "Indirizzo", "Comune", prezzo_col, "Distanza (km)", "Km in più",
                "Risparmio sul prezzo (€)", "Effetto Brent (€)", "Costo del viaggio (€)", "Risparmio netto (€)", "Peso arco", "Peso arco (≥ 0)",
                "Convenienza prezzo", "Convenienza prezzo (posizione)", "Età prezzo (gg)", "id", "lat", "lon"]
        cols = [c for c in cols if c in tab.columns]
        export = tab[cols].copy()
        export.insert(0, "origine_lat", self.origin[0])
        export.insert(1, "origine_lon", self.origin[1])

        with style.card("edges"):
            c = st.columns([1, 0.2], vertical_alignment="center")
            with c[0]:
                style.title(f"Archi origine → distributore · {len(tab)}")
            c[1].download_button("Scarica CSV",
                                 export.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                                 file_name="archi_pesati.csv", mime="text/csv", width="stretch")
            st.dataframe(
                tab[cols], hide_index=True, height=480, width="stretch",
                column_config={
                    prezzo_col: st.column_config.NumberColumn(format="%.3f"),
                    "Distanza (km)": st.column_config.NumberColumn(format="%.1f"),
                    "Km in più": st.column_config.NumberColumn(format="%.1f"),
                    "Risparmio sul prezzo (€)": st.column_config.NumberColumn(format="%+.2f"),
                    "Effetto Brent (€)": st.column_config.NumberColumn(format="%+.2f"),
                    "Costo del viaggio (€)": st.column_config.NumberColumn(format="%.2f"),
                    "Risparmio netto (€)": st.column_config.NumberColumn(format="%+.2f"),
                    "Peso arco": st.column_config.NumberColumn(format="%+.2f"),
                    "Peso arco (≥ 0)": st.column_config.NumberColumn(format="%.2f"),
                    "Convenienza prezzo": st.column_config.NumberColumn(format="%.2f"),
                    "Convenienza prezzo (posizione)": st.column_config.NumberColumn(format="%.2f"),
                    "Età prezzo (gg)": st.column_config.NumberColumn(format="%.1f"),
                },
            )
            st.caption("Risparmio netto = risparmio sul prezzo + effetto Brent − costo del viaggio. «Peso arco» è il "
                       "risparmio netto con il segno cambiato, per cercare il cammino minimo; «Peso arco (≥ 0)» è lo "
                       "stesso spostato perché non sia mai negativo. «Convenienza prezzo» va da 1 (il più economico "
                       "della zona) a 0 (il più caro).")
