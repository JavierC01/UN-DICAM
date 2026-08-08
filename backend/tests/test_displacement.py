import cv2
import numpy as np

from app.dic.displacement import calcular_desplazamiento_nodo, rastrear_malla


def _patron_speckle_suave() -> np.ndarray:
    rng = np.random.default_rng(7)
    ruido = rng.integers(0, 256, size=(160, 160), dtype=np.uint8)
    return cv2.GaussianBlur(ruido, (5, 5), 1.2)


def test_calcular_desplazamiento_nodo_recupera_subpixel():
    patron = _patron_speckle_suave()
    tx, ty = 2.4, -1.3
    matriz = np.array([[1, 0, tx], [0, 1, ty]], dtype=np.float64)
    desplazada = cv2.warpAffine(
        patron, matriz, (patron.shape[1], patron.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    resultado = calcular_desplazamiento_nodo(patron, desplazada, centro=(80, 80), subset_size=25, search_range=6)

    assert abs(resultado.u_px - tx) < 0.35
    assert abs(resultado.v_px - ty) < 0.35
    assert resultado.coef_correlacion > 0.85


def test_rastrear_malla_procesa_todos_los_nodos_sin_desplazamiento():
    patron = _patron_speckle_suave()
    nodos = [{"x": 60.0, "y": 60.0}, {"x": 100.0, "y": 100.0}, {"x": 60.0, "y": 100.0}]

    resultados = rastrear_malla(patron, patron, nodos, subset_size=21, search_range=5)

    assert len(resultados) == 3
    for resultado in resultados:
        assert abs(resultado.u_px) < 0.3
        assert abs(resultado.v_px) < 0.3
        assert resultado.coef_correlacion > 0.99
