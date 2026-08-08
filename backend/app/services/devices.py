import base64
from pathlib import Path

import cv2

from app.schemas.device import CameraInfo, OpenDeviceRequest, VideoFrameResponse, VideoSourceResponse


class DeviceServiceError(RuntimeError):
    pass


class DeviceService:
    def list_cameras(self, max_devices: int = 5) -> list[CameraInfo]:
        cameras: list[CameraInfo] = []
        for camera_id in range(max_devices):
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                continue
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
            cameras.append(CameraInfo(id=camera_id, nombre=f"Camara USB {camera_id}", ancho=width, alto=height, fps=fps))
            cap.release()
        return cameras

    def open_source(self, payload: OpenDeviceRequest) -> VideoSourceResponse:
        source = int(payload.source_id) if payload.type == "camera" else str(payload.source_id)
        if payload.type == "file" and not Path(str(source)).exists():
            raise DeviceServiceError("El archivo de video no existe")

        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW if payload.type == "camera" else cv2.CAP_ANY)
        if not cap.isOpened():
            raise DeviceServiceError("No se pudo abrir la fuente de video")

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

    def open_capture_for_source_id(self, source_id: int | str) -> cv2.VideoCapture:
        is_camera = isinstance(source_id, int) or (isinstance(source_id, str) and source_id.isdigit())
        source: int | str = int(source_id) if is_camera else source_id
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW if is_camera else cv2.CAP_ANY)
        if not cap.isOpened():
            raise DeviceServiceError("No se pudo abrir la fuente de video para el analisis")
        return cap

    def get_first_frame(self, source_id: str) -> VideoFrameResponse:
        source: int | str = int(source_id) if source_id.isdigit() else source_id
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW if isinstance(source, int) else cv2.CAP_ANY)
        if not cap.isOpened():
            raise DeviceServiceError("No se pudo abrir la fuente de video")

        ok, frame = cap.read()
        cap.release()
        if not ok:
            raise DeviceServiceError("No se pudo leer el primer frame")

        encoded_ok, buffer = cv2.imencode(".jpg", frame)
        if not encoded_ok:
            raise DeviceServiceError("No se pudo codificar el frame")
        return VideoFrameResponse(source_id=source_id, image_base64=base64.b64encode(buffer).decode("ascii"))
