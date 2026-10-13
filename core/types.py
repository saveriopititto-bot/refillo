"""Contratti di tipo e parametri del modello."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TypedDict

import pandas as pd

SCONTO_MAX = 0.10
VELOCITA_MEDIA_KMH = 40.0  # per i minuti di viaggio quando OSRM non li dà


@dataclass(slots=True)
class ModelParams:
    """Parametri di configurazione del calcolo di scoring."""

    v_tot: float = 50.0
    livello: float = 0.25
    litri: float | None = None
    alpha: float = 0.2
    delta_brent: float = 0.0
    consumo_l100: float = 5.0
    usura_eur_km: float = 0.05
    road_factor: float = 1.3
    raggio_km: float = 20.0
    use_osrm: bool = True
    ref_mode: str = "mediana"
    theta: float = 0.0
    livello_min: float = 0.10
    sconto_max: float | None = SCONTO_MAX
    valore_tempo: float = 10.0  # €/ora: il tempo per andare al distributore e tornare conta come costo (0 = no)
    autostrade: bool = False  # includere i distributori «Autostradale» del MIMIT

    @property
    def litri_effettivi(self) -> float:
        cap = self.v_tot * (1 - self.livello)
        return cap if self.litri is None else float(min(self.litri, cap))


class ModelSummary(TypedDict, total=False):
    """Riepilogo del calcolo eseguito da compute_edges."""

    n: int
    q: float
    riserva: bool
    p_market: float
    c_km: float
    best: pd.Series
    consiglio: bool
    motivo: str
    p_min: float
    p_max: float
    best_route: list[list[float]]
    vicino: pd.Series  # il distributore più vicino: riferimento del risparmio
    p_rif: float  # il suo prezzo


class BrentYfResult(TypedDict):
    """Risultato del download della serie storica del Brent da Yahoo Finance."""

    data_t: pd.Timestamp
    data_tn: pd.Timestamp
    b_t: float
    b_tn: float
    fx_t: float
    fx_tn: float


class BrentScoreResult(TypedDict):
    """Score del petrolio letto dalla tabella Supabase."""

    data: pd.Timestamp
    esito: int
    score: float
    brent_eur: float
    media_30_eur: float
    aggiornato_il: pd.Timestamp
