import pytest

from app.dic import rastreo
from app.dic.rastreo import construir_malla, generar_mascara, indice_nodo_central, triangular
from app.schemas.tracking import MeshRequest
from app.services.tracking import TrackingService
from tests.formas import ENTALLA, FORMA_L, HUESO_DE_PERRO, RECTANGULO


def _dentro(mascara, x, y) -> bool:
    return mascara[int(round(y)), int(round(x))] > 0


def test_build_mesh_returns_9_valid_nodes_for_rectangle():
    service = TrackingService()
    payload = MeshRequest(
        project_id="test",
        frame_width=200,
        frame_height=100,
        subset_size=21,
        puntos=[{"x": 20, "y": 20}, {"x": 180, "y": 20}, {"x": 180, "y": 80}, {"x": 20, "y": 80}],
    )

    result = service.build_mesh(payload)

    assert len(result.nodos) == 9
    assert all(result.validos)
    assert result.area_px == 9600


def test_build_mesh_respeta_filas_y_columnas_del_usuario():
    payload = MeshRequest(
        project_id="test",
        frame_width=200,
        frame_height=100,
        filas=4,
        columnas=6,
        subset_size=21,
        puntos=[{"x": 20, "y": 20}, {"x": 180, "y": 20}, {"x": 180, "y": 80}, {"x": 20, "y": 80}],
    )

    result = TrackingService().build_mesh(payload)

    assert len(result.nodos) == 24
    assert (result.filas, result.columnas) == (4, 6)


@pytest.mark.parametrize("forma", [RECTANGULO, FORMA_L, HUESO_DE_PERRO, ENTALLA])
def test_subset_de_nodos_validos_cae_entero_dentro_de_la_forma(forma):
    subset = 25
    malla = construir_malla(300, 300, forma, filas=8, columnas=8, subset_size=subset)
    mascara = generar_mascara(300, 300, forma)
    half = subset // 2

    for nodo, valido in zip(malla.nodos, malla.validos):
        x, y = int(nodo["x"]), int(nodo["y"])
        subset_dentro = (mascara[y - half : y - half + subset, x - half : x - half + subset] > 0).all()
        assert valido == subset_dentro


def test_forma_l_marca_invalidos_en_el_hueco_sin_moverlos_al_borde():
    malla = construir_malla(300, 300, FORMA_L, filas=6, columnas=6, subset_size=21)
    mascara = generar_mascara(300, 300, FORMA_L)

    invalidos = [n for n, v in zip(malla.nodos, malla.validos) if not v]
    assert invalidos, "el cuadrante vacio de la L debe dejar nodos invalidos"
    assert any(not _dentro(mascara, n["x"], n["y"]) for n in invalidos)
    # La grilla conserva su forma: los nodos invalidos no se proyectan al borde del poligono.
    assert len({n["x"] for n in malla.nodos}) == 6 and len({n["y"] for n in malla.nodos}) == 6


@pytest.mark.parametrize("forma", [FORMA_L, HUESO_DE_PERRO, ENTALLA])
def test_triangulacion_no_cruza_fuera_de_la_forma(forma):
    malla = construir_malla(300, 300, forma, filas=10, columnas=10, subset_size=15)
    triangulos = triangular(malla.nodos, malla.validos, malla.mascara)

    assert triangulos
    for tri in triangulos:
        assert all(malla.validos[i] for i in tri)
        cx = sum(malla.nodos[i]["x"] for i in tri) / 3
        cy = sum(malla.nodos[i]["y"] for i in tri) / 3
        assert _dentro(malla.mascara, cx, cy)


def test_triangulacion_en_l_no_tapa_el_hueco():
    malla = construir_malla(300, 300, FORMA_L, filas=10, columnas=10, subset_size=15)
    triangulos = triangular(malla.nodos, malla.validos, malla.mascara)
    # Ningun triangulo tiene su centroide en el cuadrante vacio (x > 120, y < 180).
    for tri in triangulos:
        cx = sum(malla.nodos[i]["x"] for i in tri) / 3
        cy = sum(malla.nodos[i]["y"] for i in tri) / 3
        assert not (cx > 125 and cy < 175)


def test_nodo_central_es_el_valido_mas_cercano_al_centroide():
    malla = construir_malla(300, 300, FORMA_L, filas=7, columnas=7, subset_size=21)
    cx, cy = rastreo.centroide_poligono(FORMA_L)
    idx = indice_nodo_central(malla.nodos, malla.validos, FORMA_L)

    assert malla.validos[idx]
    distancia = lambda n: (n["x"] - cx) ** 2 + (n["y"] - cy) ** 2
    assert distancia(malla.nodos[idx]) == min(distancia(n) for n, v in zip(malla.nodos, malla.validos) if v)


def test_centroide_de_rectangulo():
    assert rastreo.centroide_poligono(RECTANGULO) == pytest.approx((150, 150))


def test_region_menor_que_el_subset_falla():
    with pytest.raises(ValueError):
        construir_malla(300, 300, [{"x": 10, "y": 10}, {"x": 30, "y": 10}, {"x": 30, "y": 30}], subset_size=32)
