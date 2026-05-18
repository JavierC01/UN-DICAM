from typing import Literal

from pydantic import BaseModel


class OpenDeviceRequest(BaseModel):
    type: Literal["camera", "file"]
    source_id: int | str


class CameraInfo(BaseModel):
    id: int
    nombre: str
    ancho: int
    alto: int
    fps: float


class VideoSourceResponse(BaseModel):
    source_id: int | str
    source_type: str
    width: int
    height: int
    fps: float
    duration_s: float | None = None


class VideoFrameResponse(BaseModel):
    source_id: int | str
    image_base64: str
    mime_type: str = "image/jpeg"
