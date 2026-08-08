import cv2
import numpy as np
import pytest

from app.dic.pipeline import procesar_par_frames
from app.dic.rastreo import Rastreo


def _patron_speckle_suave() -> np.ndarray:
    rng = np.random.default_rng(11)
    ruido = rng.integers(0, 256, size=(300, 300), dtype=np.uint8)
    return cv2.GaussianBlur(ruido, (5, 5), 1.2)


def _malla_nodos() -> list[dict[str, float]]:
    rastreo = Rastreo(frame_width=300, frame_height=300)
    malla = rastreo.construir_malla(
        [
            {"x": 60, "y": 60},
            {"x": 240, "y": 60},
            {"x": 240, "y": 240},
            {"x": 60, "y": 240},
        ]
    )
    return malla.nodos


def test_procesar_par_frames_traslacion_rigida():
    patron = _patron_speckle_suave()
    nodos = _malla_nodos()
    tx, ty = 3.0, -2.0
    matriz = np.array([[1, 0, tx], [0, 1, ty]], dtype=np.float64)
    desplazada = cv2.warpAffine(
        patron, matriz, (patron.shape[1], patron.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    resultado = procesar_par_frames(patron, desplazada, nodos, mm_por_px=0.5, subset_size=25, search_range=6)

    assert len(resultado.nodos) == 9
    assert resultado.coef_correlacion_medio > 0.85
    assert resultado.u_mm_centro == pytest.approx(tx * 0.5, abs=0.2)
    assert resultado.v_mm_centro == pytest.approx(ty * 0.5, abs=0.2)
    assert resultado.campo.eps_xx_medio == pytest.approx(0.0, abs=0.01)
    assert resultado.campo.eps_yy_medio == pytest.approx(0.0, abs=0.01)
