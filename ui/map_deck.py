"""Costruzione della mappa interattiva PyDeck per i distributori e i percorsi."""
from __future__ import annotations

import math

import pandas as pd
import pydeck as pdk

import style
from ui.formatters import _hex_rgb, _it, eur, num


def build_fuel_deck(
    origin: tuple[float, float],
    edges: pd.DataFrame,
    best_route: list[list[float]] | None = None,
    show_all_lines: bool = False,
    raggio: float = 20.0,
) -> pdk.Deck:
    """Costruisce l'oggetto pdk.Deck pronto per st.pydeck_chart."""
    smin, smax = edges.score.min(), edges.score.max()
    lo_rgb, hi_rgb = _hex_rgb(style.ORANGE), _hex_rgb(style.BLUE_GREEN)

    def colore(s: float) -> list[int]:
        t = 1.0 if smax == smin else (s - smin) / (smax - smin)
        return [int(a + (b - a) * t) for a, b in zip(lo_rgb, hi_rgb)] + [220]

    mappa = edges.copy()
    mappa["colore"] = mappa.score.map(colore)
    mappa["etichetta"] = (
        mappa.bandiera + " · " + mappa.nome + "\n" + mappa.prezzo.map(lambda x: _it(f"{x:.3f}") + " €/l")
        + " · risparmio " + mappa.risparmio.map(lambda x: eur(x, sign=True))
        + " · " + mappa.dist_km.map(lambda x: num(x) + " km")
    )
    mappa["src"] = [[origin[1], origin[0]] for _ in range(len(mappa))]
    mappa["tgt"] = mappa[["lon", "lat"]].values.tolist()

    layers: list[pdk.Layer] = []
    if show_all_lines:
        layers.append(
            pdk.Layer("LineLayer", data=mappa, get_source_position="src", get_target_position="tgt",
                      get_color="colore", get_width=2, width_min_pixels=1)
        )

    if best_route:
        route_df = pd.DataFrame([{"path": best_route}])
        layers.append(
            pdk.Layer(
                "PathLayer",
                data=route_df,
                get_path="path",
                get_color=list(_hex_rgb(style.DEEP)) + [200],
                width_scale=1,
                width_min_pixels=3,
                width_max_pixels=8,
                get_width=15,
            )
        )

    layers.extend([
        pdk.Layer("ScatterplotLayer", data=mappa, get_position=["lon", "lat"], get_fill_color="colore",
                  get_radius=120, radius_min_pixels=5, radius_max_pixels=14, pickable=True),
        pdk.Layer("ScatterplotLayer", data=pd.DataFrame([{"lat": origin[0], "lon": origin[1]}]),
                  get_position=["lon", "lat"], get_fill_color=list(_hex_rgb(style.DEEP)) + [255],
                  get_radius=150, radius_min_pixels=8, radius_max_pixels=16),
    ])

    zoom = max(5.0, 12.2 - math.log2(max(raggio, 2) / 5))
    return pdk.Deck(
        layers=layers,
        map_style="light",
        initial_view_state=pdk.ViewState(latitude=origin[0], longitude=origin[1], zoom=zoom),
        tooltip={"text": "{etichetta}"},
    )
