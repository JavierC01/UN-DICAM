import pytest

from app.dic.strain import calcular_deformaciones


def _grilla_3x3(paso_mm: float = 10.0) -> list[dict[str, float]]:
    return [{"x": x * paso_mm, "y": y * paso_mm} for y in range(3) for x in range(3)]


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


def test_requiere_exactamente_9_nodos():
    with pytest.raises(ValueError):
        calcular_deformaciones([{"x": 0.0, "y": 0.0}], [(0.0, 0.0)])
