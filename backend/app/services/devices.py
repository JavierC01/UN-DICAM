import base64
import hashlib
import sys
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

import cv2

from app.Core.config import settings
from app.schemas.device import CameraInfo, OpenDeviceRequest, VideoFrameResponse, VideoSourceResponse

EXTENSIONES_VIDEO = (".mp4", ".mov", ".avi", ".mkv", ".m4v", ".webm", ".3gp")


class DeviceServiceError(RuntimeError):
    pass


def directorio_uploads() -> Path:
    ruta = Path(settings.STORAGE_DIR) / "uploads"
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _api_camara() -> int:
    # CAP_DSHOW solo existe en Windows; en Linux las camaras USB se abren con V4L2.
    if sys.platform == "win32":
        return cv2.CAP_DSHOW
    if sys.platform.startswith("linux"):
        return cv2.CAP_V4L2
    return cv2.CAP_ANY


def es_camara(source_id: int | str) -> bool:
    return isinstance(source_id, int) or (isinstance(source_id, str) and source_id.isdigit())


def ruta_video(source_id: str) -> Path:
    """Resuelve un video subido. Solo acepta nombres de archivo dentro de storage/uploads/, nunca rutas."""
    nombre = str(source_id)
    if Path(nombre).name != nombre or nombre.startswith("."):
        raise DeviceServiceError("El video debe ser un archivo subido con POST /devices/upload")
    ruta = directorio_uploads() / nombre
    if not ruta.is_file():
        raise DeviceServiceError("El archivo de video no existe")
    return ruta


def hash_video(source_id: int | str) -> str | None:
    if es_camara(source_id):
        return None
    sha = hashlib.sha256()
    with ruta_video(str(source_id)).open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1 << 20), b""):
            sha.update(bloque)
    return sha.hexdigest()


class DeviceService:
    def list_cameras(self, max_devices: int = 5) -> list[CameraInfo]:
        cameras: list[CameraInfo] = []
        for camera_id in range(max_devices):
            cap = cv2.VideoCapture(camera_id, _api_camara())
            if not cap.isOpened():
                cap.release()
                continue
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            cameras.append(CameraInfo(id=camera_id, nombre=f"Camara USB {camera_id}", ancho=width, alto=height, fps=fps))
            cap.release()
        return cameras

    def save_upload(self, nombre_original: str, contenido: BinaryIO) -> str:
        """Guarda el video en storage/uploads/ con un nombre nuevo y devuelve ese nombre (el source_id)."""
        extension = Path(nombre_original or "").suffix.lower()
        if extension not in EXTENSIONES_VIDEO:
            raise DeviceServiceError(f"Extension de video no permitida. Usa: {', '.join(EXTENSIONES_VIDEO)}")
        limite = settings.MAX_UPLOAD_MB * 1024 * 1024
        nombre = f"{uuid4().hex}{extension}"
        destino = directorio_uploads() / nombre
        escritos = 0
        try:
            with destino.open("wb") as salida:
                for bloque in iter(lambda: contenido.read(1 << 20), b""):
                    escritos += len(bloque)
                    if escritos > limite:
                        raise DeviceServiceError(f"El video supera el limite de {settings.MAX_UPLOAD_MB} MB")
                    salida.write(bloque)
        except BaseException:
            destino.unlink(missing_ok=True)
            raise

        cap = cv2.VideoCapture(str(destino), cv2.CAP_ANY)
        legible = cap.isOpened() and cap.read()[0]
        cap.release()
        if not legible:
            destino.unlink(missing_ok=True)
            raise DeviceServiceError("El archivo no es un video legible")
        return nombre

    def open_capture_for_source_id(self, source_id: int | str) -> cv2.VideoCapture:
        if es_camara(source_id):
            cap = cv2.VideoCapture(int(source_id), _api_camara())
        else:
            cap = cv2.VideoCapture(str(ruta_video(str(source_id))), cv2.CAP_ANY)
        if not cap.isOpened():
            raise DeviceServiceError("No se pudo abrir la fuente de video")
        return cap

    def open_source(self, payload: OpenDeviceRequest) -> VideoSourceResponse:
        if payload.type == "camera" and not es_camara(payload.source_id):
            raise DeviceServiceError("El id de camara debe ser numerico")
        if payload.type == "file" and es_camara(payload.source_id):
            raise DeviceServiceError("El video debe ser un archivo subido con POST /devices/upload")
        cap = self.open_capture_for_source_id(payload.source_id)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        duration_s = (frame_count / fps) if payload.type == "file" and fps > 0 else None
        cap.release()

        return VideoSourceResponse(
            source_id=payload.source_id,
            source_type=payload.type,
            width=width,
            height=height,
            fps=fps,
            duration_s=duration_s,
        )

    def get_first_frame(self, source_id: str) -> VideoFrameResponse:
        cap = self.open_capture_for_source_id(source_id)
        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise DeviceServiceError("No se pudo leer el primer frame")

        encoded_ok, buffer = cv2.imencode(".jpg", frame)
        if not encoded_ok:
            raise DeviceServiceError("No se pudo codificar el frame")
        return VideoFrameResponse(source_id=source_id, image_base64=base64.b64encode(buffer).decode("ascii"))
