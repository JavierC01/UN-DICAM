import math

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.services.devices import DeviceService
from app.workers import tasks
from tests.formas import RECTANGULO

FPS = 10.0
AREA_MM2 = 15.0
MODULO_MPA = 12000.0
EPS_POR_FRAME = 0.002


class _FakeCapture:
    """Sustituye cv2.VideoCapture en los tests: entrega una lista de frames en memoria."""

    def __init__(self, frames: list[np.ndarray], fps: float = FPS) -> None:
        self._frames = frames
        self._fps = fps
        self._idx = 0

    def get(self, prop: int) -> float:
        if prop == cv2.CAP_PROP_FRAME_COUNT:
            return float(len(self._frames))
        if prop == cv2.CAP_PROP_FPS:
            return self._fps
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


def _frames_estirados(n: int = 6) -> list[np.ndarray]:
    """Estiramiento uniforme conocido en y: frame k tiene eps_yy = k * EPS_POR_FRAME."""
    rng = np.random.default_rng(3)
    patron = cv2.GaussianBlur(rng.integers(0, 256, size=(300, 300), dtype=np.uint8), (5, 5), 1.2)
    frames = []
    for k in range(n):
        matriz = np.array([[1, 0, 0], [0, 1 + k * EPS_POR_FRAME, 0]], dtype=np.float64)
        deformada = cv2.warpAffine(patron, matriz, (300, 300), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        frames.append(cv2.cvtColor(deformada, cv2.COLOR_GRAY2BGR))
    return frames


def _csv_maquina(n: int = 6) -> bytes:
    """Carga lineal con la deformacion (F = E * eps * A), en kN y con una fila ilegible."""
    filas = ["tiempo;fuerza"]
    for i in range(0, 10 * n):
        t = i / (10 * FPS)
        filas.append(f"{t:.3f};{MODULO_MPA * EPS_POR_FRAME * t * FPS * AREA_MM2 / 1000:.6f}".replace(".", ","))
    filas.insert(3, "---;---")
    return "\n".join(filas).encode()


def _configurar_proyecto(client: TestClient, fuente_carga: str = "ninguna", roi=None) -> str:
    project_id = client.post("/api/v1/projects", json={"name": "Probeta madera"}).json()["id"]
    if fuente_carga == "archivo":
        columnas = client.post(
            f"/api/v1/loads/{project_id}/archivo", files={"file": ("maquina.csv", _csv_maquina(), "text/csv")}
        )
        assert columnas.status_code == 200
        assert columnas.json() == {**columnas.json(), "configurado": False, "columnas": ["tiempo", "fuerza"]}
        importado = client.post(
            f"/api/v1/loads/{project_id}/archivo",
            files={"file": ("maquina.csv", _csv_maquina(), "text/csv")},
            data={"columna_tiempo": "tiempo", "columna_carga": "fuerza", "unidad_tiempo": "s", "unidad_carga": "kN"},
        )
        assert importado.status_code == 200, importado.text
        assert importado.json()["filas_descartadas"] == 1

    specimen = client.post(
        "/api/v1/specimen/configure",
        json={
            "project_id": project_id,
            "long_calibracion_px": 100,
            "long_calibracion_mm": 100,
            "ancho_mm": 5,
            "espesor_mm": 3,
            "long_calibre_mm": 100,
            "tipo_ensayo": "traccion",
            "fuente_carga": fuente_carga,
            "roi_carga": roi,
        },
    )
    assert specimen.status_code == 200, specimen.text

    mesh = client.post(
        "/api/v1/tracking/mesh",
        json={"project_id": project_id, "frame_width": 300, "frame_height": 300, "puntos": RECTANGULO,
              "filas": 4, "columnas": 4, "subset_size": 25},
    )
    assert mesh.status_code == 200
    assert all(mesh.json()["validos"])

    puntos = client.put(
        f"/api/v1/tracking/{project_id}/puntos-ensayo", json={"puntos": [{"x": 150, "y": 90}, {"x": 150, "y": 210}]}
    )
    assert puntos.status_code == 200, puntos.text
    return project_id


def _analizar(client: TestClient, project_id: str) -> str:
    started = client.post(
        "/api/v1/analysis/start",
        json={"project_id": project_id, "source_id": 0, "subset_size": 25, "search_range": 6, "frame_inicio": 0},
    )
    assert started.status_code == 200
    task_id = started.json()["task_id"]
    assert client.get(f"/api/v1/analysis/status/{task_id}").json()["status"] == "success"
    return task_id


def test_flujo_traccion_con_carga_de_la_maquina(client, monkeypatch):
    frames = _frames_estirados()
    monkeypatch.setattr(DeviceService, "open_capture_for_source_id", lambda self, source_id: _FakeCapture(frames))
    project_id = _configurar_proyecto(client, fuente_carga="archivo")

    task_id = _analizar(client, project_id)

    body = client.get(f"/api/v1/analysis/results/{task_id}").json()
    assert body["carga"] == {"fuente": "archivo", "interpolados": 5, "descartados": 0, "frames_con_carga": 5}
    ensayo = body["ensayo"]
    assert ensayo["tipo"] == "traccion" and ensayo["ajuste"] is None
    for k, (eps, sigma) in enumerate(zip(ensayo["curva"]["x"], ensayo["curva"]["y"]), start=1):
        assert eps == pytest.approx(k * EPS_POR_FRAME, abs=4e-4)
        assert sigma == pytest.approx(MODULO_MPA * k * EPS_POR_FRAME, rel=1e-3)
    # Ejes corregidos: x = desplazamiento, y = carga.
    assert body["curva_desplaz_carga"]["y"][0] == pytest.approx(MODULO_MPA * EPS_POR_FRAME * AREA_MM2, rel=1e-3)
    assert body["coef_correlacion_medio"] > 0.8
    assert body["mapa_yy_url"] == f"/storage/analyses/{task_id}/mapa_yy.jpg"
    meta = body["metadatos"]
    assert meta["parametros"]["subset_size"] == 25 and meta["calibracion"]["mm_por_px"] == 1.0
    assert meta["carga"]["archivo"]["mapeo"]["unidad_carga"] == "kN" and len(meta["carga"]["archivo"]["sha256"]) == 64
    assert any("hash del video" in a for a in body["advertencias"])

    ajuste = client.post(f"/api/v1/analysis/{task_id}/propiedad", json={"x_min": 0, "x_max": 0.02})
    assert ajuste.status_code == 200, ajuste.text
    assert ajuste.json()["pendiente"] == pytest.approx(MODULO_MPA, rel=0.08)
    assert ajuste.json()["r2"] > 0.99
    assert client.get(f"/api/v1/analysis/results/{task_id}").json()["ensayo"]["ajuste"]["n_puntos"] == 5
    assert client.post(f"/api/v1/analysis/{task_id}/propiedad", json={}).status_code == 400

    csv = client.get(f"/api/v1/export/csv/{task_id}")
    assert csv.status_code == 200 and csv.headers["content-type"].startswith("text/csv")
    assert "# " in csv.text and "carga_N" in csv.text and "sha256" in csv.text
    jpg = client.get(f"/api/v1/export/jpg/{task_id}")
    assert jpg.status_code == 200 and jpg.content[:2] == b"\xff\xd8"
    pdf = client.get(f"/api/v1/export/pdf/{task_id}")
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"

    historial = client.get(f"/api/v1/projects/{project_id}/analyses").json()
    assert [a["id"] for a in historial] == [task_id] and historial[0]["status"] == "success"
    proyecto = client.get(f"/api/v1/projects/{project_id}").json()
    assert proyecto["status"] == "completed"


def test_sin_fuente_de_carga_la_carga_es_nula_no_cero(client, monkeypatch):
    frames = _frames_estirados(3)
    monkeypatch.setattr(DeviceService, "open_capture_for_source_id", lambda self, source_id: _FakeCapture(frames))
    task_id = _analizar(client, _configurar_proyecto(client))

    body = client.get(f"/api/v1/analysis/results/{task_id}").json()
    assert body["curva_desplaz_carga"]["y"] == [None, None]
    assert body["esfuerzo_max_mpa"] is None
    assert any("Sin fuente de carga" in a for a in body["advertencias"])


def test_ocr_fallido_descarta_el_punto_y_lo_cuenta(client, monkeypatch):
    frames = _frames_estirados(4)
    monkeypatch.setattr(DeviceService, "open_capture_for_source_id", lambda self, source_id: _FakeCapture(frames))
    lecturas = iter([150.0, ValueError("sin lectura"), 450.0])

    def _ocr_falso(frame, roi):
        valor = next(lecturas)
        if isinstance(valor, Exception):
            raise valor
        return valor

    monkeypatch.setattr(tasks, "extract_load_value", _ocr_falso)
    roi = {"x": 0, "y": 0, "width": 50, "height": 20}
    task_id = _analizar(client, _configurar_proyecto(client, fuente_carga="ocr", roi=roi))

    body = client.get(f"/api/v1/analysis/results/{task_id}").json()
    assert body["curva_desplaz_carga"]["y"] == [150.0, None, 450.0]
    assert body["carga"]["fallos_ocr"] == 1 and body["carga"]["frames_con_carga"] == 2
    assert any("OCR" in a for a in body["advertencias"])


def test_ocr_sin_roi_y_archivo_sin_importar_se_rechazan(client):
    project_id = client.post("/api/v1/projects", json={"name": "x"}).json()["id"]
    base = {"project_id": project_id, "long_calibracion_px": 1, "long_calibracion_mm": 1, "ancho_mm": 1,
            "espesor_mm": 1, "long_calibre_mm": 1}
    assert client.post("/api/v1/specimen/configure", json={**base, "fuente_carga": "ocr"}).status_code == 422
    assert client.post("/api/v1/specimen/configure", json={**base, "fuente_carga": "archivo"}).status_code == 400
    assert client.post("/api/v1/specimen/configure", json={**base, "tipo_ensayo": "portico"}).status_code == 422


def test_puntos_del_ensayo_fuera_de_la_malla_se_rechazan(client):
    project_id = _configurar_proyecto(client)
    fuera = client.put(
        f"/api/v1/tracking/{project_id}/puntos-ensayo", json={"puntos": [{"x": 150, "y": 90}, {"x": 10, "y": 10}]}
    )
    assert fuera.status_code == 400
    incompleto = client.put(f"/api/v1/tracking/{project_id}/puntos-ensayo", json={"puntos": [{"x": 150, "y": 90}]})
    assert incompleto.status_code == 400


def test_analisis_fallido_marca_proyecto_failed(client, monkeypatch):
    def _sin_video(self, source_id):
        raise tasks.DeviceServiceError("camara desconectada")

    monkeypatch.setattr(DeviceService, "open_capture_for_source_id", _sin_video)
    project_id = _configurar_proyecto(client)
    client_sin_excepciones = TestClient(client.app, raise_server_exceptions=False, headers=client.headers)

    client_sin_excepciones.post("/api/v1/analysis/start", json={"project_id": project_id, "source_id": 0})

    assert client.get(f"/api/v1/projects/{project_id}").json()["status"] == "failed"
    assert client.get(f"/api/v1/projects/{project_id}/analyses").json()[0]["status"] == "failed"


def test_start_analysis_sin_configuracion_falla(client):
    project = client.post("/api/v1/projects", json={"name": "Sin calibrar"}).json()

    response = client.post("/api/v1/analysis/start", json={"project_id": project["id"], "source_id": 0})

    assert response.status_code == 400


def test_subida_de_video_y_rutas_restringidas(client, tmp_path):
    ruta = tmp_path / "ensayo.avi"
    escritor = cv2.VideoWriter(str(ruta), cv2.VideoWriter_fourcc(*"MJPG"), FPS, (64, 48))
    for _ in range(3):
        escritor.write(np.full((48, 64, 3), 128, dtype=np.uint8))
    escritor.release()

    subido = client.post("/api/v1/devices/upload", files={"file": ("ensayo.avi", ruta.read_bytes(), "video/x-msvideo")})
    assert subido.status_code == 201, subido.text
    source_id = subido.json()["source_id"]
    assert source_id.endswith(".avi") and "/" not in source_id
    assert subido.json()["width"] == 64 and math.isclose(subido.json()["fps"], FPS)
    assert client.get(f"/api/v1/devices/frame/{source_id}").status_code == 200

    assert client.post("/api/v1/devices/upload", files={"file": ("x.txt", b"hola", "text/plain")}).status_code == 400
    assert client.post("/api/v1/devices/upload", files={"file": ("x.mp4", b"no es video", "video/mp4")}).status_code == 400
    for ruta_maliciosa in ("../../etc/passwd", "/etc/passwd", ".env"):
        assert client.post("/api/v1/devices/open", json={"type": "file", "source_id": ruta_maliciosa}).status_code == 400
