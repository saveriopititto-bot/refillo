"""Funzioni di formattazione per numeri e valuta in formato italiano."""
from __future__ import annotations


def _it(s: str) -> str:
    """Converte formato numerico anglosassone (punto decimale, virgola migliaia) in italiano."""
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def eur(x: float, d: int = 2, sign: bool = False) -> str:
    """Formatta un numero come importo in euro (es. '+1,50 €' o '1,50 €')."""
    return _it(f"{x:{'+' if sign else ''},.{d}f}") + " €"


def num(x: float, d: int = 1) -> str:
    """Formatta un numero con decimali in stile italiano (es. '15,0')."""
    return _it(f"{x:,.{d}f}")


def _hex_rgb(h: str) -> tuple[int, int, int]:
    """Converte un colore esadecimale '#RRGGBB' in tupla (R, G, B)."""
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
