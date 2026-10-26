from pydantic import BaseModel, Field, model_validator

from app.schemas.common import Point


class MeshRequest(BaseModel):
    frame_width: int = Field(gt=0)
    frame_height: int = Field(gt=0)
    puntos: list[Point] = Field(min_length=3)
    project_id: str
    # Mas nodos = mapa de deformacion mas fino, pero mas lento y con subsets que se solapan.
    filas: int = Field(default=3, ge=2, le=20)
    columnas: int = Field(default=3, ge=2, le=20)
    # Los nodos solo son validos donde el subset completo cae dentro del poligono.
    subset_size: int = Field(default=32, ge=5, le=255)

    @model_validator(mode="after")
    def puntos_dentro_del_frame(self):
        if any(p.x > self.frame_width or p.y > self.frame_height for p in self.puntos):
            raise ValueError("Todos los puntos del poligono deben estar dentro del frame")
        return self


class MeshResponse(BaseModel):
    nodos: list[Point]
    validos: list[bool]
    poligono: list[Point]
    area_px: float
    filas: int
    columnas: int
    subset_size: int
    puntos_ensayo: list[Point] | None = None


class PuntosEnsayoRequest(BaseModel):
    puntos: list[Point]


class TrackingValidationResponse(BaseModel):
    valid: bool
    area_px: float
    message: str
