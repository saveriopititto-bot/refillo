"""Client per Yahoo Finance (Brent ed EUR/USD)."""
from __future__ import annotations

import pandas as pd

from core.types import BrentYfResult


def fetch_brent_yf(n_days: int) -> BrentYfResult:
    """Scarica Brent (BZ=F) ed EUR/USD da Yahoo Finance. Richiede `yfinance`."""
    import yfinance as yf

    start = pd.Timestamp.today().normalize() - pd.Timedelta(days=int(n_days) + 15)

    def serie(ticker: str) -> pd.Series:
        s = yf.Ticker(ticker).history(start=start)["Close"].dropna()
        if s.empty:
            raise ValueError(f"Nessun dato per {ticker}")
        s.index = s.index.tz_localize(None).normalize()
        return s

    def valore_a(s: pd.Series, giorno: pd.Timestamp) -> float:
        s = s[s.index <= giorno]
        if s.empty:
            raise ValueError("Storico insufficiente")
        return float(s.iloc[-1])

    brent, fx = serie("BZ=F"), serie("EURUSD=X")
    t = min(brent.index[-1], fx.index[-1])
    tn = t - pd.Timedelta(days=int(n_days))
    return {
        "data_t": t, "data_tn": tn,
        "b_t": valore_a(brent, t), "b_tn": valore_a(brent, tn),
        "fx_t": valore_a(fx, t), "fx_tn": valore_a(fx, tn),
    }
