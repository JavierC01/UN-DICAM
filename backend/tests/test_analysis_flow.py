import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.services.devices import DeviceService


class _FakeCapture:
    """Sustituye cv2.VideoCapture en los tests: entrega una lista de frames en memoria."""

    def __init__(self, frames: list[np.ndarray]) -> None:
        self._frames = frames
        self._idx = 0

    def get(self, prop: int) -> float:
        if prop == cv2.CAP_PROP_FRAME_COUNT:
            return float(len(self._frames))
        return 0.0

    def set(self, prop: int, value: float) -> bool:
        if prop == cv2.CAP_PROP_POS_FRAMES:
            self._idx = int(value)
        return True

    def read(self) -> tuple[bool, np.ndarray | None]:
        if self._idx >= len(self._frames):
            return False, None
        frame = self._frames[self._idx]
        self._idx += 1
        return True, frame

    def release(self) -> None:
        pass


def _frames_sinteticos() -> list[np.ndarray]:
    rng = np.random.default_rng(3)
    patron = cv2.GaussianBlur(rng.integers(0, 256, size=(300, 300), dtype=np.uint8), (5, 5), 1.2)
    frames = []
    for ty in (0.0, 1.5, 3.0, 4.5):
        matriz = np.array([[1, 0, 0], [0, 1, ty]], dtype=np.float64)
        desplazada = cv2.warpAffine(
            patron, matriz, (patron.shape[1], patron.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        frames.append(cv2.cvtColor(desplazada, cv2.COLOR_GRAY2BGR))
    return frames


def test_flujo_completo_de_analisis(monkeypatch):
    frames = _frames_sinteticos()
    monkeypatch.setattr(
        DeviceService, "open_capture_for_source_id", lambda self, source_id: _FakeCapture(frames)
    )

    client = TestClient(app)

    project = client.post("/api/v1/projects", json={"name": "Probeta acero"}).json()
    project_id = project["id"]

    specimen = client.post(
        "/api/v1/specimen/configure",
        json={
            "project_id": project_id,
            "long_calibracion_px": 100,
            "long_calibracion_mm": 25,
            "ancho_mm": 5,
            "espesor_mm": 3,
            "long_calibre_mm": 25,
        },
    )
    assert specimen.status_code == 200

    mesh = client.post(
        "/api/v1/tracking/mesh",
        json={
            "project_id": project_id,
            "frame_width": 300,
            "frame_height": 300,
            "puntos": [
                {"x": 60, "y": 60},
                {"x": 240, "y": 60},
                {"x": 240, "y": 240},
                {"x": 60, "y": 240},
            ],
        },
    )
    assert mesh.status_code == 200
    assert len(mesh.json()["nodos"]) == 9

    started = client.post(
        "/api/v1/analysis/start",
        json={
            "project_id": project_id,
            "source_id": 0,
            "subset_size": 25,
            "search_range": 6,
            "frame_inicio": 0,
        },
    )
    assert started.status_code == 200
    task_id = started.json()["task_id"]

    status_response = client.get(f"/api/v1/analysis/status/{task_id}")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "success"

    results = client.get(f"/api/v1/analysis/results/{task_id}")
    assert results.status_code == 200
    body = results.json()
    assert len(body["curva_esfuerzo_strain"]["x"]) == 3
    assert body["coef_correlacion_medio"] > 0.8
    assert body["mapa_yy_url"] == f"/storage/analyses/{task_id}/mapa_yy.jpg"

    projects_after = client.get("/api/v1/projects").json()
    assert next(p for p in projects_after if p["id"] == project_id)["status"] == "completed"


def test_start_analysis_sin_configuracion_falla(monkeypatch):
    client = TestClient(app)
    project = client.post("/api/v1/projects", json={"name": "Sin calibrar"}).json()

    response = client.post(
        "/api/v1/analysis/start",
        json={"project_id": project["id"], "source_id": 0},
    )

    assert response.status_code == 400
