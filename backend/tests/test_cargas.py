import io
import math

import pandas as pd
import pytest

from app.cargas.importador import ImportacionCargaError, extraer_serie, leer_tabla
from app.cargas.sincronizacion import cargas_en_frames


def test_csv_con_punto_y_coma_coma_decimal_y_kn():
    contenido = "Tiempo (s);Fuerza (kN)\n0,0;0,0\n0,5;1,5\nerror;x\n1,0;3,0\n".encode()
    tabla = leer_tabla(contenido, "maquina.csv")

    tiempos, cargas, descartadas = extraer_serie(tabla, "Tiempo (s)", "Fuerza (kN)", "s", "kN")

    assert tiempos == [0.0, 0.5, 1.0]
    assert cargas == [0.0, 1500.0, 3000.0]
    assert descartadas == 1


def test_xlsx_en_milisegundos_y_kgf():
    buffer = io.BytesIO()
    pd.DataFrame({"t_ms": [0, 100, 200], "F_kgf": [0, 10, 20]}).to_excel(buffer, index=False)

    tiempos, cargas, _ = extraer_serie(leer_tabla(buffer.getvalue(), "ensayo.xlsx"), "t_ms", "F_kgf", "ms", "kgf")

    assert tiempos == pytest.approx([0.0, 0.1, 0.2])
    assert cargas == pytest.approx([0.0, 98.0665, 196.133])


def test_errores_de_importacion():
    tabla = leer_tabla(b"t,F\n0,1\n1,2\n", "a.csv")
    with pytest.raises(ImportacionCargaError):
        extraer_serie(tabla, "t", "no_existe", "s", "N")
    with pytest.raises(ImportacionCargaError):
        extraer_serie(tabla, "t", "F", "horas", "N")
    with pytest.raises(ImportacionCargaError):
        extraer_serie(leer_tabla(b"t,F\n1,1\n0,2\n", "a.csv"), "t", "F", "s", "N")
    with pytest.raises(ImportacionCargaError):
        leer_tabla(b"x", "a.pdf")


def test_interpolacion_a_tiempos_de_frame_con_offset():
    tiempos = [0.0, 1.0, 2.0, 3.0]
    cargas = [0.0, 100.0, 200.0, 300.0]

    valores, interpolados, descartados = cargas_en_frames([0.0, 0.25, 1.5, 2.9], tiempos, cargas, offset_s=0.5)

    assert valores[:3] == pytest.approx([50.0, 75.0, 200.0])
    assert math.isnan(valores[3])  # 2.9 + 0.5 cae fuera del registro
    assert (interpolados, descartados) == (3, 1)


def test_evento_de_inicio_por_umbral_de_carga():
    tiempos = [0.0, 1.0, 2.0, 3.0, 4.0]
    cargas = [0.0, 0.0, 10.0, 60.0, 110.0]

    valores, _, _ = cargas_en_frames([0.0, 1.0], tiempos, cargas, evento_inicio="umbral_carga", umbral_n=10.0)

    assert valores == pytest.approx([10.0, 60.0])
    with pytest.raises(ValueError):
        cargas_en_frames([0.0], tiempos, cargas, evento_inicio="umbral_carga", umbral_n=1000.0)
