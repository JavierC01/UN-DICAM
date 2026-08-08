import numpy as np

from app.dic.correlation import mapa_correlacion, pico_entero, zncc


def _patron_speckle() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.integers(0, 256, size=(140, 140), dtype=np.uint8)


def test_zncc_es_uno_para_subsets_identicos():
    patron = _patron_speckle()
    subset = patron[40:70, 40:70]

    assert abs(zncc(subset, subset) - 1.0) < 1e-9


def test_zncc_es_cero_para_ventana_uniforme():
    patron = _patron_speckle()
    subset = patron[40:70, 40:70]
    ventana_uniforme = np.full_like(subset, 128)

    assert zncc(subset, ventana_uniforme) == 0.0


def test_mapa_correlacion_encuentra_desplazamiento_entero():
    patron = _patron_speckle()
    desplazada = np.roll(np.roll(patron, 3, axis=1), -2, axis=0)

    mapa = mapa_correlacion(patron, desplazada, centro=(70, 70), subset_size=21, search_range=8)
    i, j, coef = pico_entero(mapa)

    assert i - 8 == 3
    assert j - 8 == -2
    assert coef > 0.99


def test_mapa_correlacion_rechaza_subset_fuera_de_limites():
    patron = _patron_speckle()

    try:
        mapa_correlacion(patron, patron, centro=(5, 5), subset_size=21, search_range=8)
        assert False, "se esperaba ValueError"
    except ValueError:
        pass
