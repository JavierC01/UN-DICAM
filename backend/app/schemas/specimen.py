from pydantic import BaseModel, Field


class SpecimenConfigRequest(BaseModel):
    project_id: str
    long_calibracion_px: float = Field(gt=0)
    long_calibracion_mm: float = Field(gt=0)
    ancho_mm: float = Field(gt=0)
    espesor_mm: float = Field(gt=0)
    long_calibre_mm: float = Field(gt=0)
    roi_carga: dict | None = None


class SpecimenConfigResponse(BaseModel):
    px_por_mm: float
    mm_por_px: float
    area_mm2: float
    confirmado: bool
