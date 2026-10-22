from pydantic import BaseModel, Field, field_validator

from app.schemas.common import Point


class MeshRequest(BaseModel):
    frame_width: int = Field(gt=0)
    frame_height: int = Field(gt=0)
    puntos: list[Point] = Field(min_length=3)
    project_id: str
    # Mas nodos = mapa de deformacion mas fino, pero mas lento y con subsets que se solapan.
    filas: int = Field(default=3, ge=2, le=20)
    columnas: int = Field(default=3, ge=2, le=20)

    @field_validator("puntos")
    @classmethod
    def points_must_fit_frame(cls, puntos: list[Point], info):
        return puntos


class MeshResponse(BaseModel):
    nodos: list[Point]
    poligono: list[Point]
    area_px: float
    filas: int
    columnas: int


class TrackingValidationResponse(BaseModel):
    valid: bool
    area_px: float
    message: str
