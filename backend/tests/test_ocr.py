import shutil

import cv2
import numpy as np
import pytest

from app.dic.ocr import extract_load_value, parsear_valor_numerico, recortar_roi

_TESSERACT_DISPONIBLE = shutil.which("tesseract") is not None


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("125.4 N", 125.4),
        ("  -3,2 kg  ", -3.2),
        ("Carga: 980", 980.0),
    ],
)
def test_parsear_valor_numerico_extrae_el_numero(texto, esperado):
    assert parsear_valor_numerico(texto) == pytest.approx(esperado)


def test_parsear_valor_numerico_sin_numero_lanza_error():
    with pytest.raises(ValueError):
        parsear_valor_numerico("sin lectura")


def test_recortar_roi_fuera_de_limites_lanza_error():
    imagen = np.zeros((100, 100, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        recortar_roi(imagen, {"x": 90, "y": 90, "width": 50, "height": 50})


def test_recortar_roi_devuelve_la_subregion():
    imagen = np.zeros((100, 100, 3), dtype=np.uint8)
    imagen[10:30, 10:30] = 255
    recorte = recortar_roi(imagen, {"x": 10, "y": 10, "width": 20, "height": 20})
    assert recorte.shape[:2] == (20, 20)
    assert (recorte == 255).all()


@pytest.mark.skipif(not _TESSERACT_DISPONIBLE, reason="Tesseract OCR no esta instalado en este entorno")
def test_extract_load_value_lee_numero_renderizado():
    imagen = np.full((80, 240, 3), 255, dtype=np.uint8)
    cv2.putText(imagen, "482.5", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)

    valor = extract_load_value(imagen, {"x": 0, "y": 0, "width": 240, "height": 80})

    assert valor == pytest.approx(482.5, abs=5)
