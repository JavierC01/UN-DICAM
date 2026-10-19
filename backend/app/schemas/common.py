from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)


class RoiCarga(BaseModel):
    """Region del frame donde el video muestra el valor de carga (celda de carga en pantalla)."""

    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
