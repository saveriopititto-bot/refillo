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


def _data(r) -> str:
    """« del 12/10»: quando il gestore ha comunicato il prezzo (vuoto se non si sa)."""
    d = getattr(r, "dt_comu", None)
    return f" del {d:%d/%m}" if d is not None and not pd.isna(d) else ""


def _minuti(r) -> str:
    m = getattr(r, "minuti", None)
    return f" · {max(1, round(m))} min" if m is not None and not pd.isna(m) else ""


def _popup(r, unita: str = "l") -> str:
    """Riquadro che si apre toccando il distributore: dati principali e link al navigatore."""
    nome = escape(r.bandiera or r.nome or "Distributore")
    impianto = f"<br>{escape(r.nome)}" if r.nome and r.nome != r.bandiera else ""
    return (
        f'<div style="font-family:Archivo,sans-serif;font-size:13px;line-height:1.4;color:{style.DEEP}">'
        f"<b>{r.rank}. {nome}</b>{impianto}<br>{escape(r.indirizzo)}, {escape(r.comune)}<br>"
        f"<b>{_it(f'{r.prezzo:.3f}')} €/{unita}</b>{_data(r)} · {num(r.dist_km)} km{_minuti(r)}<br>"
        f"risparmio {eur(r.risparmio, sign=True)} rispetto al più vicino<br>"
        f'<a href="{NAVIGA_URL.format(lat=r.lat, lon=r.lon)}" target="_blank" rel="noopener" '
        f'style="display:inline-block;margin-top:6px;font-weight:700;color:{style.A700}">Portami qui →</a></div>'
    )


def build_fuel_map(
    origin: tuple[float, float],
    edges: pd.DataFrame,
    best_route: list[list[float]] | None = None,
    show_all_lines: bool = False,
    unita: str = "l",
) -> folium.Map:
    """Mappa con i distributori colorati per convenienza, la posizione e il percorso (GeoJSON [lon, lat])."""
    # zoom a passi di un quarto: l'inquadratura sui distributori lascia meno margine
    m = folium.Map(location=list(origin), tiles=None, prefer_canvas=True, zoom_control=True, zoom_snap=0.25,
                   zoom_delta=0.5)
    m.default_js, m.default_css = LEAFLET_JS, LEAFLET_CSS
    folium.TileLayer(TILES, attr=ATTRIBUZIONE, max_zoom=19).add_to(m)
    smin, smax = edges.score.min(), edges.score.max()

    def colore(score: float) -> str:
        return _colore(1.0 if smax == smin else (score - smin) / (smax - smin))

    if show_all_lines:
        for r in edges.itertuples():
            folium.PolyLine([origin, (r.lat, r.lon)], color=colore(r.score), weight=1, opacity=0.5).add_to(m)

    if best_route:
        folium.PolyLine([(lat, lon) for lon, lat in best_route], color=style.DEEP, weight=5, opacity=0.8).add_to(m)

    # i migliori per ultimi, così restano sopra agli altri
    for r in edges.sort_values("score").itertuples():
        migliore = r.rank == 1
        folium.CircleMarker(
            location=(r.lat, r.lon), radius=10 if migliore else 7,
            color=style.DEEP if migliore else "#ffffff", weight=3 if migliore else 1,
            fill=True, fill_color=colore(r.score), fill_opacity=0.95,
            popup=folium.Popup(_popup(r, unita), max_width=260),
        ).add_to(m)

    folium.CircleMarker(location=origin, radius=9, color="#ffffff", weight=3, fill=True, fill_color=style.DEEP,
                        fill_opacity=1, popup=folium.Popup("Sei qui")).add_to(m)

    # inquadratura sul percorso verso il migliore (posizione, distributore migliore e strada): gli altri distributori
    # restano sulla mappa, basta allontanarsi; zoom massimo 16 se il migliore è a due passi
    best = edges.loc[edges["rank"] == 1].iloc[0] if (edges["rank"] == 1).any() else edges.iloc[0]
    lats, lons = [origin[0], best.lat], [origin[1], best.lon]
    if best_route:
        lats += [lat for _, lat in best_route]
        lons += [lon for lon, _ in best_route]
    # margine più largo in alto a sinistra (pulsanti + e −) e in basso (scritta OpenStreetMap)
    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]], padding_top_left=(52, 40),
                 padding_bottom_right=(32, 36), max_zoom=16)
    return m


def map_html(m: folium.Map) -> str:
    """Pagina HTML completa della mappa, alta quanto la cornice che la contiene (la proporzione la dà il CSS)."""
    m.get_root().header.add_child(folium.Element(
        f"<style>html,body{{margin:0;height:100%}}.folium-map{{height:100%!important}}{SFONDO_CSS}</style>"))
    return m.get_root().render()
