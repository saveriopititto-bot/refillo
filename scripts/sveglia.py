"""Tiene sveglia l'app su Streamlit Community Cloud: la apre con Chromium e, se dorme, tocca il pulsante per riaccenderla.

Streamlit Cloud spegne le app dopo qualche ora senza visite: chi la apre (anche dall'icona dell'app installata) vede
«This app has gone to sleep». Lanciato ogni 6 ore da .github/workflows/sveglia.yml. Tocca anche il pulsante d'avvio,
così i dati del giorno restano già in memoria per chi arriva dopo (la posizione non c'è: l'app usa la stima o Roma).

    python scripts/sveglia.py [indirizzo]
"""
from __future__ import annotations

import re
import sys
import time

from playwright.sync_api import Page, sync_playwright

URL = "https://refillo.streamlit.app/"
ATTESA_APP_S = 240   # dopo il risveglio Streamlit Cloud reinstalla e riavvia l'app: può volerci qualche minuto
ATTESA_HOME_S = 120  # download dei dati del giorno dopo il pulsante d'avvio
RISVEGLIO = re.compile(r"get this app back up", re.I)


def _cerca(pagina: Page, selettore: str):
    """Il primo elemento visibile in qualunque frame (su Streamlit Cloud l'app sta in un iframe)."""
    for frame in pagina.frames:
        try:
            el = frame.locator(selettore).first
            if el.count() and el.is_visible():
                return el
        except Exception:  # frame che si ricarica mentre lo si guarda
            continue
    return None


def sveglia(url: str) -> bool:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pagina = browser.new_page(viewport={"width": 390, "height": 740})
        pagina.goto(url, wait_until="domcontentloaded", timeout=60_000)

        fine = time.monotonic() + ATTESA_APP_S
        avvia = None
        while time.monotonic() < fine:
            pulsante = pagina.get_by_role("button", name=RISVEGLIO)
            if pulsante.count() and pulsante.first.is_visible():
                print("L'app dormiva: la riaccendo.")
                pulsante.first.click()
            avvia = _cerca(pagina, ".st-key-avvia button:visible")
            if avvia:
                break
            pagina.wait_for_timeout(3000)
        if not avvia:
            print(f"L'app non si è aperta entro {ATTESA_APP_S} s.")
            browser.close()
            return False
        print("App sveglia.")

        # facoltativo: carica i dati del giorno, così restano in memoria
        avvia.click()
        fine = time.monotonic() + ATTESA_HOME_S
        while time.monotonic() < fine and not _cerca(pagina, ".st-key-metriche"):
            pagina.wait_for_timeout(3000)
        print("Home pronta." if _cerca(pagina, ".st-key-metriche") else "Home non pronta in tempo (l'app è comunque sveglia).")
        browser.close()
        return True


if __name__ == "__main__":
    sys.exit(0 if sveglia(sys.argv[1] if len(sys.argv) > 1 else URL) else 1)
