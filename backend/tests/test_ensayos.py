import math

import pytest

from app.dic.ensayos import ENSAYOS, ajuste_lineal, obtener_ensayo


def test_traccion_extensometro_mide_deformacion_entre_dos_puntos():
    ensayo = obtener_ensayo("traccion")
    puntos = [(0.0, 0.0), (0.0, 50.0)]
    eps = 0.004
    desplaz = [(0.0, 0.0), (0.0, eps * 50.0)]

    assert ensayo.medir(puntos, desplaz, {}) == pytest.approx(eps)
    assert ensayo.calcular_respuesta(1500.0, 15.0, {}) == pytest.approx(100.0)


def test_compresion_da_acortamiento_positivo():
    puntos = [(0.0, 0.0), (0.0, 50.0)]
    assert obtener_ensayo("compresion").medir(puntos, [(0.0, 0.0), (0.0, -0.1)], {}) == pytest.approx(0.002)


def test_flexion_deflexion_relativa_a_los_apoyos():
    puntos = [(0.0, 0.0), (500.0, 0.0), (1000.0, 0.0)]
    # Movimiento rigido de 1 mm hacia abajo + 3 mm de flecha en el centro.
    desplaz = [(0.0, 1.0), (0.0, 4.0), (0.0, 1.0)]
    assert obtener_ensayo("flexion").medir(puntos, desplaz, {}) == pytest.approx(3.0)


def test_cortante_deslizamiento_relativo_en_el_eje_de_carga():
    ensayo = obtener_ensayo("cortante")
    desplaz = [(0.1, 0.2), (0.4, 1.7)]
    assert ensayo.medir([(0, 0), (10, 0)], desplaz, {"eje_carga": "y"}) == pytest.approx(1.5)
    assert ensayo.medir([(0, 0), (10, 0)], desplaz, {"eje_carga": "x"}) == pytest.approx(0.3)
    with pytest.raises(ValueError):
        ensayo.validar_parametros({"eje_carga": "z"})


def test_portico_rotacion_y_momento():
    ensayo = obtener_ensayo("portico")
    theta = 0.01
    puntos = [(0.0, 0.0), (100.0, 0.0)]
    # Giro rigido de theta alrededor del primer punto.
    desplaz = [(0.0, 0.0), (100 * math.cos(theta) - 100, 100 * math.sin(theta))]

    assert ensayo.medir(puntos, desplaz, {"brazo_mm": 800}) == pytest.approx(theta)
    assert ensayo.calcular_respuesta(10.0, 1.0, {"brazo_mm": 800}) == pytest.approx(8000.0)
    with pytest.raises(ValueError):
        ensayo.validar_parametros({})


def test_medida_con_desplazamiento_faltante_es_nan():
    assert math.isnan(obtener_ensayo("traccion").medir([(0, 0), (0, 50)], [(math.nan, math.nan), (0, 0)], {}))


def test_todos_los_ensayos_describen_sus_ejes():
    for ensayo in ENSAYOS.values():
        d = ensayo.describir()
        assert d["n_puntos"] >= 2 and d["medida"]["unidad"] and d["propiedad"]["unidad"]
    with pytest.raises(ValueError):
        obtener_ensayo("torsion")


def test_ajuste_lineal_recupera_modulo_y_r2_en_rango_de_x():
    e = 12000.0
    x = [i * 1e-4 for i in range(30)]
    y = [e * v if v <= 2e-3 else e * 2e-3 for v in x] + [None]  # zona lineal y luego meseta; un punto nulo
    x = x + [None]

    ajuste = ajuste_lineal(x, y, x_min=0.0, x_max=1.5e-3)

    assert ajuste["pendiente"] == pytest.approx(e)
    assert ajuste["r2"] == pytest.approx(1.0)
    assert ajuste["n_puntos"] == 16
    assert ajuste["rango"] == {"tipo": "x", "min": 0.0, "max": 1.5e-3}


def test_ajuste_lineal_por_fraccion_de_la_respuesta_maxima():
    x = [i * 0.1 for i in range(11)]
    y = [100.0 * v for v in x]  # maximo 100

    ajuste = ajuste_lineal(x, y, fraccion_min=0.1, fraccion_max=0.4)

    assert ajuste["pendiente"] == pytest.approx(100.0)
    assert ajuste["n_puntos"] == 4
    assert ajuste["rango"]["respuesta_max"] == pytest.approx(100.0)


def test_ajuste_lineal_exige_rango_y_puntos_suficientes():
    with pytest.raises(ValueError):
        ajuste_lineal([0, 1, 2], [0, 1, 2])
    with pytest.raises(ValueError):
        ajuste_lineal([0, 1, 2], [0, 1, 2], x_min=0, x_max=0.5)
