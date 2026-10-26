from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.dic.ensayos import TIPOS_ENSAYO, obtener_ensayo
from app.schemas.common import RoiCarga

TipoEnsayo = Literal[TIPOS_ENSAYO]
FuenteCarga = Literal["ninguna", "ocr", "archivo"]


class SpecimenConfigRequest(BaseModel):
    project_id: str
    long_calibracion_px: float = Field(gt=0)
    long_calibracion_mm: float = Field(gt=0)
    ancho_mm: float = Field(gt=0)
    espesor_mm: float = Field(gt=0)
    long_calibre_mm: float = Field(gt=0)
    roi_carga: RoiCarga | None = None
    tipo_ensayo: TipoEnsayo = "traccion"
    parametros_ensayo: dict = Field(default_factory=dict)
    fuente_carga: FuenteCarga = "ninguna"

    @model_validator(mode="after")
    def validar_ensayo_y_carga(self):
        obtener_ensayo(self.tipo_ensayo).validar_parametros(self.parametros_ensayo)
        if self.fuente_carga == "ocr" and self.roi_carga is None:
            raise ValueError("La lectura de carga por OCR necesita la region de carga (roi_carga)")
        return self


class SpecimenConfigResponse(BaseModel):
    px_por_mm: float
    mm_por_px: float
    area_mm2: float
    confirmado: bool
    long_calibracion_px: float | None = None
    long_calibracion_mm: float | None = None
    ancho_mm: float | None = None
    espesor_mm: float | None = None
    long_calibre_mm: float | None = None
    roi_carga: RoiCarga | None = None
    tipo_ensayo: str = "traccion"
    parametros_ensayo: dict = Field(default_factory=dict)
    fuente_carga: str = "ninguna"
