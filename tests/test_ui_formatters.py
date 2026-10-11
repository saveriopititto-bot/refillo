from ui.formatters import _hex_rgb, _it, eur, num


def test_it_inverte_virgola_e_punto():
    assert _it("1,234.56") == "1.234,56"
    assert _it("100.0") == "100,0"


def test_eur_formattazione():
    assert eur(1.50) == "1,50 €"
    assert eur(-2.4, sign=True) == "-2,40 €"
    assert eur(3.0, sign=True) == "+3,00 €"
    assert eur(1234.5, d=2) == "1.234,50 €"


def test_num_formattazione():
    assert num(15.0, 1) == "15,0"
    assert num(1250.0, 0) == "1.250"


def test_hex_rgb():
    assert _hex_rgb("#ffffff") == (255, 255, 255)
    assert _hex_rgb("#000000") == (0, 0, 0)
    assert _hex_rgb("#fb8500") == (251, 133, 0)
