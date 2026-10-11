"""Modello di scoring per il calcolo di convenienza del rifornimento."""
from __future__ import annotations

import numpy as np
import pandas as pd

from clients.osrm import get_osrm_distances, get_osrm_route
from core.geo import haversine_km
from core.types import ModelParams, ModelSummary


def brent_delta(b_t: float, b_tn: float, eurusd_t: float = 1.0, eurusd_tn: float = 1.0, clip: float = 0.10) -> float:
    """Variazione relativa del Brent in euro, limitata a +-clip.

    b_* in USD/barile; eurusd_* = dollari per 1 euro (quotazione EUR/USD).
    """
    e_t, e_tn = b_t / eurusd_t, b_tn / eurusd_tn
    return float(np.clip((e_t - e_tn) / e_tn, -clip, clip))


def compute_edges(
    cands: pd.DataFrame,
    origin: tuple[float, float],
    p: ModelParams,
) -> tuple[pd.DataFrame, ModelSummary]:
    """Pesi degli archi origine -> distributore.

    Restituisce (tabella ordinata per score decrescente, riepilogo).
    Colonne chiave: score = S_i (da massimizzare), peso = -S_i (costo per
    cammino minimo), peso_pos = S_max - S_i (costo non negativo).
    """
    olat, olon = origin
    df = cands.copy()
    df["dist_km"] = haversine_km(olat, olon, df.lat.values, df.lon.values) * p.road_factor
    df = df[df.dist_km <= p.raggio_km].copy()

    if p.use_osrm and not df.empty:
        # Prendi i 99 più vicini per rispettare i limiti di OSRM (1 origin + 99 dest = 100)
        cands_idx = df.nsmallest(99, "dist_km").index
        dests = list(zip(df.loc[cands_idx, "lat"], df.loc[cands_idx, "lon"]))

        real_dists = get_osrm_distances(origin, dests)

        for idx, d in zip(cands_idx, real_dists):
            if d is not None:
                df.at[idx, "dist_km"] = d

        df = df[df.dist_km <= p.raggio_km].copy()

    summary: ModelSummary = {
        "n": len(df),
        "q": p.litri_effettivi,
        "riserva": p.livello < p.livello_min,
    }
    if df.empty:
        return df, summary

    p_market = float(df.prezzo.median() if p.ref_mode == "mediana" else df.prezzo.mean())
    if p.sconto_max is not None:
        df = df[df.prezzo >= p_market - p.sconto_max - 1e-9].copy()
        summary["n"] = len(df)
        if df.empty:
            return df, summary
    c_km = p.consumo_l100 / 100 * p_market + p.usura_eur_km
    q = p.litri_effettivi

    df["dev_km"] = 2 * df.dist_km

    df["guadagno"] = q * (p_market - df.prezzo)
    df["brent"] = q * p.alpha * p_market * p.delta_brent
    df["costo_log"] = df.dev_km * c_km
    df["score"] = df.guadagno + df.brent - df.costo_log
    df["risparmio"] = df.guadagno - df.costo_log  # quello che si risparmia davvero, senza l'effetto Brent
    df["peso"] = -df.score
    df["peso_pos"] = df.score.max() - df.score

    pmin, pmax = df.prezzo.min(), df.prezzo.max()
    df["ep"] = 1.0 if pmax == pmin else 1 - (df.prezzo - pmin) / (pmax - pmin)
    n = len(df)
    df["ep_pct"] = 1.0 if n == 1 else 1 - (df.prezzo.rank(method="average") - 1) / (n - 1)

    df = df.sort_values("score", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", np.arange(1, n + 1))

    best = df.iloc[0]
    sicurezza = p.livello < p.livello_min
    if sicurezza:
        consiglio, motivo = True, f"carburante nel serbatoio sotto la soglia di riserva ({p.livello:.0%} < {p.livello_min:.0%})"
    elif best.score > p.theta:
        consiglio, motivo = True, f"il risparmio migliore ({best.score:+.2f} €) supera la soglia di convenienza ({p.theta:.2f} €)"
    else:
        consiglio, motivo = False, f"il risparmio migliore ({best.score:+.2f} €) non supera la soglia di convenienza ({p.theta:.2f} €)"
    summary.update(
        p_market=p_market,
        c_km=c_km,
        best=best,
        consiglio=consiglio,
        motivo=motivo,
        p_min=float(pmin),
        p_max=float(pmax),
        riserva=sicurezza,
    )
    summary["best_route"] = get_osrm_route(origin, (best.lat, best.lon)) if p.use_osrm else []

    return df, summary
