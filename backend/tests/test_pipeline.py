import math

import cv2
import numpy as np
import pytest

from app.dic.pipeline import procesar_par_frames
from app.dic.rastreo import construir_malla, preparar_geometria
from tests.formas import FORMA_L, RECTANGULO


def _patron_speckle_suave() -> np.ndarray:
    rng = np.random.default_rng(11)
    ruido = rng.integers(0, 256, size=(300, 300), dtype=np.uint8)
    return cv2.GaussianBlur(ruido, (5, 5), 1.2)


def _geometria(forma, subset: int, filas: int = 3, columnas: int = 3):
    malla = construir_malla(300, 300, forma, filas=filas, columnas=columnas, subset_size=subset)
    return preparar_geometria(malla.nodos, malla.validos, forma, 300, 300, subset)


def _deformar(patron: np.ndarray, matriz: np.ndarray) -> np.ndarray:
    return cv2.warpAffine(
        patron, matriz, (patron.shape[1], patron.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def test_procesar_par_frames_traslacion_rigida():
    patron = _patron_speckle_suave()
    geometria = _geometria(RECTANGULO, subset=25)
    tx, ty = 3.0, -2.0
    desplazada = _deformar(patron, np.array([[1, 0, tx], [0, 1, ty]], dtype=np.float64))

    resultado = procesar_par_frames(patron, desplazada, geometria, mm_por_px=0.5, subset_size=25, search_range=6)

    assert len(resultado.nodos) == 9
    assert resultado.nodos_perdidos == 0
    assert resultado.coef_correlacion_medio > 0.85
    assert resultado.u_mm_centro == pytest.approx(tx * 0.5, abs=0.2)
    assert resultado.v_mm_centro == pytest.approx(ty * 0.5, abs=0.2)
    assert resultado.campo.eps_xx_medio == pytest.approx(0.0, abs=0.01)
    assert resultado.campo.eps_yy_medio == pytest.approx(0.0, abs=0.01)


def test_estiramiento_uniforme_en_forma_l():
    """Imagen sintetica con eps_yy conocido sobre una forma en L: los nodos del hueco no se rastrean."""
    patron = _patron_speckle_suave()
    geometria = _geometria(FORMA_L, subset=21, filas=6, columnas=6)
    eps = 0.02
    estirada = _deformar(patron, np.array([[1, 0, 0], [0, 1 + eps, 0]], dtype=np.float64))  # y_def = (1+eps) y_ref

    resultado = procesar_par_frames(patron, estirada, geometria, mm_por_px=1.0, subset_size=21, search_range=8)

    assert geometria.validos.count(False) > 0
    assert all(r is None for r, v in zip(resultado.nodos, geometria.validos) if not v)
    assert resultado.campo.eps_yy_medio == pytest.approx(eps, abs=0.003)
    assert resultado.campo.eps_xx_medio == pytest.approx(0.0, abs=0.003)
    assert math.isfinite(resultado.v_mm_centro)
