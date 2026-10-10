import io
import tarfile

import pandas as pd
import pytest

import fuel_model as fm
import storico
from test_fuel_model import ANAG, PREZZI


@pytest.fixture
def dati():
    anag, extraction = fm.parse_anagrafica(ANAG.encode())
    return anag, fm.parse_prezzi(PREZZI.encode()), extraction


def test_medie_giornaliere(dati):
    df = storico.medie_giornaliere(*dati)
    assert list(df.columns) == storico.COLONNE
    assert (df.data == pd.Timestamp("2026-10-09")).all()
    b = df[(df.carburante == "Benzina") & df.self].set_index("comune")
    assert b.loc["GUALDO TADINO", "mediana"] == pytest.approx(1.75)  # mediana di 1.80 e 1.70
    assert b.loc["GUALDO TADINO", "n"] == 2
    assert b.loc["ROMA", "mediana"] == pytest.approx(1.60)
    assert df[df.carburante == "Gasolio"].empty  # unico prezzo troppo vecchio


def test_medie_giornaliere_senza_data(dati):
    anag, prezzi, _ = dati
    with pytest.raises(ValueError):
        storico.medie_giornaliere(anag, prezzi, None)


def _giorno(data, prezzo):
    return pd.DataFrame([{"data": pd.Timestamp(data), "comune": "ROMA", "provincia": "RM", "carburante": "Benzina",
                          "self": True, "mediana": prezzo, "n": 3}])[storico.COLONNE]


def test_aggiorna_sostituisce_e_tiene_gli_ultimi_giorni():
    s = storico.vuoto()
    for d in pd.date_range("2026-01-01", periods=10):
        s = storico.aggiorna(s, _giorno(d, 1.7), giorni=5)
    assert s.data.nunique() == 5 and s.data.min() == pd.Timestamp("2026-01-06")
    s = storico.aggiorna(s, _giorno("2026-01-10", 1.9), giorni=5)  # stesso giorno: sostituisce
    assert len(s) == 5 and s[s.data == "2026-01-10"].mediana.item() == pytest.approx(1.9)


def test_scrivi_e_leggi(tmp_path, dati):
    df = storico.medie_giornaliere(*dati)
    f = tmp_path / "storico" / "medie.csv.gz"
    storico.scrivi(df, f)
    letto = storico.leggi(f)
    pd.testing.assert_frame_equal(letto.reset_index(drop=True), df.reset_index(drop=True), check_dtype=False)
    assert letto.self.dtype == bool
    assert storico.leggi(tmp_path / "manca.csv.gz").empty


def _tar(path, files):
    with tarfile.open(path, "w:gz") as tar:
        for nome, testo in files.items():
            b = testo.encode()
            info = tarfile.TarInfo(nome)
            info.size = len(b)
            tar.addfile(info, io.BytesIO(b))


def test_medie_da_archivio(tmp_path):
    prezzi_10 = PREZZI.replace("2026-10-09", "2026-10-10").replace("09/10/2026", "10/10/2026").replace("1.700", "1.650")
    _tar(tmp_path / "a.tar.gz", {
        "q4/anagrafica_impianti_attivi_20261009.csv": ANAG,
        "q4/prezzo_alle_8_20261009.csv": PREZZI,
        "q4/prezzo_alle_8_20261010.csv": prezzi_10,  # senza anagrafica del giorno: usa quella del 9
        "q4/leggimi.csv": "niente\ndi utile\n",
    })
    log = []
    df, comuni = storico.medie_da_archivio([tmp_path / "a.tar.gz"], log=log.append)
    assert set(comuni.comune) == {"GUALDO TADINO", "ROMA"}
    assert sorted(df.data.dt.strftime("%Y-%m-%d").unique()) == ["2026-10-09", "2026-10-10"]
    b = df[(df.carburante == "Benzina") & df.self & (df.comune == "GUALDO TADINO")].set_index("data")
    assert b.loc["2026-10-10", "mediana"] == pytest.approx(1.725)
    assert any("leggimi" in r for r in log)
    solo_10, _ = storico.medie_da_archivio([tmp_path / "a.tar.gz"], dal=pd.Timestamp("2026-10-10"), log=log.append)
    assert solo_10.data.nunique() == 1


def test_centri_comuni_e_unione(tmp_path, dati):
    anag = dati[0]
    c = storico.centri_comuni(anag)
    gualdo = c[c.comune == "GUALDO TADINO"].iloc[0]
    assert gualdo.lat == pytest.approx(43.235) and gualdo.provincia == "PG"
    vecchi = pd.DataFrame([{"comune": "SPARITO", "provincia": "XX", "lat": 40.0, "lon": 10.0},
                           {"comune": "ROMA", "provincia": "RM", "lat": 1.0, "lon": 1.0}])
    u = storico.unisci_comuni(vecchi, c)
    assert "SPARITO" in set(u.comune)  # i comuni non più presenti restano
    assert u[u.comune == "ROMA"].lat.item() == pytest.approx(41.9)  # vale il centro più recente
    storico.scrivi(u, tmp_path / "comuni.csv.gz")
    assert len(storico.leggi_comuni(tmp_path / "comuni.csv.gz")) == len(u)
    assert storico.leggi_comuni(tmp_path / "manca.csv.gz").empty


# ---------------------------------------------------------------- score 30 giorni
COMUNI = pd.DataFrame([{"comune": "VICINO", "provincia": "PG", "lat": 43.23, "lon": 12.78},
                       {"comune": "ACCANTO", "provincia": "PG", "lat": 43.25, "lon": 12.80},
                       {"comune": "LONTANO", "provincia": "RM", "lat": 41.90, "lon": 12.50}])


def _storico(giorni, prezzi_per_comune, fuel="Benzina", self_=True, oggi="2026-10-10"):
    righe = []
    for d in pd.date_range(end=pd.Timestamp(oggi) - pd.Timedelta(days=1), periods=giorni):
        for (comune, prov), (prezzo, n) in prezzi_per_comune.items():
            righe.append({"data": d, "comune": comune, "provincia": prov, "carburante": fuel, "self": self_,
                          "mediana": prezzo, "n": n})
    return pd.DataFrame(righe)[storico.COLONNE]


def test_media_zona_pesata_e_solo_nel_raggio():
    medie = _storico(30, {("VICINO", "PG"): (1.80, 3), ("ACCANTO", "PG"): (1.70, 1), ("LONTANO", "RM"): (1.50, 9)})
    oggi = pd.Timestamp("2026-10-10")
    medie = pd.concat([medie, _storico(1, {("VICINO", "PG"): (9.0, 3)}, oggi="2026-10-11")])  # oggi: escluso
    z = storico.media_zona(medie, COMUNI, (43.23, 12.78), 15, 1.3, "Benzina", True, oggi)
    assert z["media"] == pytest.approx((1.80 * 3 + 1.70 * 1) / 4)  # LONTANO fuori raggio, oggi escluso
    assert z["giorni"] == 30 and z["comuni"] == 2
    assert storico.media_zona(medie, COMUNI, (43.23, 12.78), 15, 1.3, "Gasolio", True, oggi)["media"] is None
    assert storico.media_zona(medie, COMUNI, (43.23, 12.78), 15, 1.3, "Benzina", False, oggi)["media"] is None


def test_media_zona_solo_ultimi_30_giorni():
    vecchi = _storico(10, {("VICINO", "PG"): (2.50, 1)}, oggi="2026-09-01")  # oltre i 30 giorni
    recenti = _storico(5, {("VICINO", "PG"): (1.80, 1)})
    z = storico.media_zona(pd.concat([vecchi, recenti]), COMUNI, (43.23, 12.78), 15, 1.3, "Benzina", True,
                           pd.Timestamp("2026-10-10"))
    assert z["media"] == pytest.approx(1.80) and z["giorni"] == 5


@pytest.mark.parametrize("prezzo, atteso", [(1.70, 1), (1.77, 0), (1.80, 0), (1.83, 0), (1.90, -1)])
def test_score_30gg(prezzo, atteso):
    score, scarto = storico.score_30gg(prezzo, 1.80, giorni=30)
    assert score == atteso and scarto == pytest.approx(prezzo / 1.80 - 1)


def test_score_30gg_soglia_esatta_e_storico_corto():
    assert storico.score_30gg(1.80 * 0.98, 1.80, 30)[0] == 1     # esattamente -2%: ottimo
    assert storico.score_30gg(1.80 * 1.02, 1.80, 30)[0] == -1    # esattamente +2%: alto
    assert storico.score_30gg(1.70, 1.80, 30, soglia=0.10)[0] == 0
    assert storico.score_30gg(1.70, 1.80, giorni=6) == (None, None)
    assert storico.score_30gg(1.70, None, giorni=30) == (None, None)
