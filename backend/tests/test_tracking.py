from app.schemas.tracking import MeshRequest
from app.dic.rastreo import Rastreo
from app.services.tracking import TrackingService


def test_build_mesh_returns_9_nodes_for_rectangle():
    service = TrackingService()
    payload = MeshRequest(
        project_id="test",
        frame_width=200,
        frame_height=100,
        puntos=[
            {"x": 20, "y": 20},
            {"x": 180, "y": 20},
            {"x": 180, "y": 80},
            {"x": 20, "y": 80},
        ],
    )

    result = service.build_mesh(payload)

    assert len(result.nodos) == 9
    assert result.area_px == 9600


def test_rastreo_core_returns_9_nodes_for_rectangle():
    rastreo = Rastreo(frame_width=200, frame_height=100)
    result = rastreo.construir_malla(
        [
            {"x": 20, "y": 20},
            {"x": 180, "y": 20},
            {"x": 180, "y": 80},
            {"x": 20, "y": 80},
        ]
    )

    assert len(result.nodos) == 9
    assert result.area_px == 9600


def test_build_mesh_respeta_filas_y_columnas_del_usuario():
    service = TrackingService()
    payload = MeshRequest(
        project_id="test",
        frame_width=200,
        frame_height=100,
        filas=4,
        columnas=6,
        puntos=[
            {"x": 20, "y": 20},
            {"x": 180, "y": 20},
            {"x": 180, "y": 80},
            {"x": 20, "y": 80},
        ],
    )

    result = service.build_mesh(payload)

    assert len(result.nodos) == 24
    assert (result.filas, result.columnas) == (4, 6)
