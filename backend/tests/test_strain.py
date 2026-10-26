import math

import pytest

from app.dic.rastreo import construir_malla, triangular
from app.dic.strain import calcular_deformaciones, deformacion_triangulos, interpolar_desplazamiento, localizar_punto
from tests.formas import FORMA_L, HUESO_DE_PERRO


def _grilla_3x3(paso_mm: float = 10.0, filas: int = 3, columnas: int = 3) -> list[dict[str, float]]:
    return [{"x": x * paso_mm, "y": y * paso_mm} for y in range(filas) for x in range(columnas)]


def test_traccion_uniforme_en_y_da_eps_yy_constante():
    nodos = _grilla_3x3()
    k = 0.01
    desplazamientos = [(0.0, k * nodo["y"]) for nodo in nodos]

    campo = calcular_deformaciones(nodos, desplazamientos)

    for fila in campo.eps_yy:
        for valor in fila:
            assert valor == pytest.approx(k)
    for fila in campo.eps_xx:
        for valor in fila:
            assert valor == pytest.approx(0.0)
    for fila in campo.eps_xy:
        for valor in fila:
            assert valor == pytest.approx(0.0)
    assert campo.eps_yy_medio == pytest.approx(k)


def test_traslacion_rigida_da_deformacion_nula():
    nodos = _grilla_3x3()
    desplazamientos = [(2.5, -1.5) for _ in nodos]

    campo = calcular_deformaciones(nodos, desplazamientos)

    assert campo.eps_xx_medio == pytest.approx(0.0)
    assert campo.eps_yy_medio == pytest.approx(0.0)
    assert campo.eps_xy_medio == pytest.approx(0.0)


def test_grilla_rectangular_da_celdas_filas_menos_uno_por_columnas_menos_uno():
    nodos = _grilla_3x3(filas=4, columnas=5)
    k = 0.02
    desplazamientos = [(k * nodo["x"], 0.0) for nodo in nodos]

    campo = calcular_deformaciones(nodos, desplazamientos, columnas=5)

    assert len(campo.eps_xx) == 3 and all(len(fila) == 4 for fila in campo.eps_xx)
    assert campo.eps_xx_medio == pytest.approx(k)


def test_celda_con_esquina_invalida_vale_nan_y_no_entra_en_la_media():
    nodos = _grilla_3x3()
    k = 0.01
    desplazamientos = [(0.0, k * n["y"]) for n in nodos]
    desplazamientos[2] = None  # esquina superior derecha invalida: afecta solo la celda (0, 1)

    campo = calcular_deformaciones(nodos, desplazamientos)

    assert math.isnan(campo.eps_yy[0][1])
    assert campo.eps_yy[0][0] == pytest.approx(k)
    assert campo.eps_yy_medio == pytest.approx(k)


def test_requiere_grilla_valida():
    with pytest.raises(ValueError):
        calcular_deformaciones([{"x": 0.0, "y": 0.0}], [(0.0, 0.0)])


@pytest.mark.parametrize("forma", [FORMA_L, HUESO_DE_PERRO])
def test_cst_reproduce_deformacion_homogenea_en_formas_no_rectangulares(forma):
    malla = construir_malla(300, 300, forma, filas=8, columnas=8, subset_size=15)
    triangulos = triangular(malla.nodos, malla.validos, malla.mascara)
    exx, eyy, gxy = 0.002, -0.004, 0.001  # campo lineal conocido: u = exx x + gxy y, v = eyy y
    desplazamientos = [
        (exx * n["x"] + gxy * n["y"], eyy * n["y"]) if v else None for n, v in zip(malla.nodos, malla.validos)
    ]

    campo = deformacion_triangulos(malla.nodos, desplazamientos, triangulos)

    assert all(v == pytest.approx(exx) for v in campo.eps_xx)
    assert all(v == pytest.approx(eyy) for v in campo.eps_yy)
    assert campo.eps_xy_medio == pytest.approx(gxy / 2)


def test_cst_triangulo_con_nodo_perdido_vale_nan():
    nodos = [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0}, {"x": 0.0, "y": 10.0}, {"x": 10.0, "y": 10.0}]
    triangulos = [(0, 1, 2), (1, 3, 2)]
    desplazamientos = [(0.0, 0.0), (0.1, 0.0), (0.0, 0.0), None]

    campo = deformacion_triangulos(nodos, desplazamientos, triangulos)

    assert campo.eps_xx[0] == pytest.approx(0.01)
    assert math.isnan(campo.eps_xx[1])
    assert campo.eps_xx_medio == pytest.approx(0.01)


def test_interpolacion_en_punto_reproduce_campo_lineal_y_falla_fuera():
    nodos = [{"x": 0.0, "y": 0.0}, {"x": 10.0, "y": 0.0}, {"x": 0.0, "y": 10.0}]
    desplazamientos = [(2 + 0.1 * n["x"], -0.2 * n["y"]) for n in nodos]

    ubicacion = localizar_punto({"x": 2.0, "y": 3.0}, nodos, [(0, 1, 2)])

    assert interpolar_desplazamiento(ubicacion, desplazamientos) == pytest.approx((2.2, -0.6))
    assert localizar_punto({"x": 9.0, "y": 9.0}, nodos, [(0, 1, 2)]) is None
    assert all(math.isnan(v) for v in interpolar_desplazamiento(None, desplazamientos))
