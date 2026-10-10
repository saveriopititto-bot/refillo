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
