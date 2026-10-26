from pydantic import BaseModel, Field


class StartAnalysisRequest(BaseModel):
    project_id: str
    source_id: int | str
    subset_size: int = Field(default=32, ge=5, le=255)
    search_range: int = Field(default=20, gt=0)
    frame_inicio: int = Field(default=0, ge=0)
    frame_fin: int | None = None


class StartAnalysisResponse(BaseModel):
    task_id: str
    status: str


class AnalysisStatusResponse(BaseModel):
    task_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    frames_procesados: int
    frames_total: int
    mensaje: str


class AnalysisSummary(BaseModel):
    id: str
    project_id: str
    status: str
    created_at: str | None = None
    params: dict | None = None


class AnalysisResultsResponse(BaseModel):
    """Los valores que faltan (carga sin leer, nodo perdido) llegan como null, nunca como 0."""

    curva_desplaz_carga: dict
    curva_esfuerzo_strain: dict
    ensayo: dict | None
    mapa_xx_url: str
    mapa_yy_url: str
    mapa_xy_url: str
    esfuerzo_max_mpa: float | None
    strain_max: float | None
    coef_correlacion_medio: float | None
    carga: dict
    advertencias: list[str]
    metadatos: dict


class AjustePropiedadRequest(BaseModel):
    """Rango del ajuste lineal: en el eje x de la curva del ensayo, o como fraccion de la respuesta maxima."""

    x_min: float | None = None
    x_max: float | None = None
    fraccion_min: float | None = Field(default=None, ge=0, le=1)
    fraccion_max: float | None = Field(default=None, ge=0, le=1)
