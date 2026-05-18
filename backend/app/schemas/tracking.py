from pydantic import BaseModel, Field, field_validator

from app.schemas.common import Point


class MeshRequest(BaseModel):
    frame_width: int = Field(gt=0)
    frame_height: int = Field(gt=0)
    puntos: list[Point] = Field(min_length=3)
    project_id: str

    @field_validator("puntos")
    @classmethod
    def points_must_fit_frame(cls, puntos: list[Point], info):
        return puntos


class MeshResponse(BaseModel):
    nodos: list[Point]
    poligono: list[Point]
    area_px: float


class TrackingValidationResponse(BaseModel):
    valid: bool
    area_px: float
    message: str
