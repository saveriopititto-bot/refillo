"""Mappa Leaflet (folium) dei distributori, della posizione e del percorso verso il migliore."""
from __future__ import annotations

from html import escape

import folium
import pandas as pd

import style
from ui.formatters import _hex_rgb, _it, eur, num

NAVIGA_URL = "https://www.google.com/maps/dir/?api=1&destination={lat:.6f},{lon:.6f}"
# sfondo OpenStreetMap standard: gratis e senza chiave (CARTO ora la chiede e mostra «API key required»).
# Schiarito e meno saturo via CSS (SFONDO_CSS), così i pallini colorati restano in evidenza.
TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
ATTRIBUZIONE = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
SFONDO_CSS = ".leaflet-tile-pane{filter:saturate(.45) brightness(1.08) contrast(.9)}.leaflet-container{background:#f2f8fb}"
# solo Leaflet e jQuery (i popup di folium lo usano): folium caricherebbe anche Bootstrap e altri file inutili qui
LEAFLET_JS = [("leaflet", "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"),
              ("jquery", "https://code.jquery.com/jquery-3.7.1.min.js")]
LEAFLET_CSS = [("leaflet_css", "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css")]


def _colore(t: float) -> str:
    """Dall'arancione (conviene meno, t = 0) al verde-blu (conviene di più, t = 1), in esadecimale."""
    lo, hi = _hex_rgb(style.ORANGE), _hex_rgb(style.BLUE_GREEN)
    return "#" + "".join(f"{int(a + (b - a) * t):02x}" for a, b in zip(lo, hi))


def _popup(r) -> str:
    """Riquadro che si apre toccando il distributore: dati principali e link al navigatore."""
    nome = escape(r.bandiera or r.nome or "Distributore")
    impianto = f"<br>{escape(r.nome)}" if r.nome and r.nome != r.bandiera else ""
    return (
        f'<div style="font-family:Archivo,sans-serif;font-size:13px;line-height:1.4;color:{style.DEEP}">'
        f"<b>{r.rank}. {nome}</b>{impianto}<br>{escape(r.indirizzo)}, {escape(r.comune)}<br>"
        f"<b>{_it(f'{r.prezzo:.3f}')} €/l</b> · {num(r.dist_km)} km · risparmio {eur(r.risparmio, sign=True)}<br>"
        f'<a href="{NAVIGA_URL.format(lat=r.lat, lon=r.lon)}" target="_blank" rel="noopener" '
        f'style="display:inline-block;margin-top:6px;font-weight:700;color:{style.A700}">Portami qui →</a></div>'
    )


def build_fuel_map(
    origin: tuple[float, float],
    edges: pd.DataFrame,
    best_route: list[list[float]] | None = None,
    show_all_lines: bool = False,
) -> folium.Map:
    """Mappa con i distributori colorati per convenienza, la posizione e il percorso (GeoJSON [lon, lat])."""
    # zoom a passi di un quarto: l'inquadratura sui distributori lascia meno margine
    m = folium.Map(location=list(origin), tiles=None, prefer_canvas=True, zoom_control=True, zoom_snap=0.25,
                   zoom_delta=0.5)
    m.default_js, m.default_css = LEAFLET_JS, LEAFLET_CSS
    folium.TileLayer(TILES, attr=ATTRIBUZIONE, max_zoom=19).add_to(m)
    smin, smax = edges.score.min(), edges.score.max()

    if show_all_lines:
        for r in edges.itertuples():
            t = 1.0 if smax == smin else (r.score - smin) / (smax - smin)
            folium.PolyLine([origin, (r.lat, r.lon)], color=_colore(t), weight=1, opacity=0.5).add_to(m)

    if best_route:
        folium.PolyLine([(lat, lon) for lon, lat in best_route], color=style.DEEP, weight=5, opacity=0.8).add_to(m)

    # i migliori per ultimi, così restano sopra agli altri
    for r in edges.sort_values("score").itertuples():
        t = 1.0 if smax == smin else (r.score - smin) / (smax - smin)
        migliore = r.rank == 1
        folium.CircleMarker(
            location=(r.lat, r.lon), radius=10 if migliore else 7,
            color=style.DEEP if migliore else "#ffffff", weight=3 if migliore else 1,
            fill=True, fill_color=_colore(t), fill_opacity=0.95,
            popup=folium.Popup(_popup(r), max_width=260),
        ).add_to(m)

    folium.CircleMarker(location=origin, radius=9, color="#ffffff", weight=3, fill=True, fill_color=style.DEEP,
                        fill_opacity=1, popup=folium.Popup("Sei qui")).add_to(m)

    lats = [origin[0], *edges.lat]
    lons = [origin[1], *edges.lon]
    if best_route:
        lats += [lat for _, lat in best_route]
        lons += [lon for lon, _ in best_route]
    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding=(16, 16))
    return m


def map_html(m: folium.Map) -> str:
    """Pagina HTML completa della mappa, alta quanto la cornice che la contiene (la proporzione la dà il CSS)."""
    m.get_root().header.add_child(folium.Element(
        f"<style>html,body{{margin:0;height:100%}}.folium-map{{height:100%!important}}{SFONDO_CSS}</style>"))
    return m.get_root().render()
