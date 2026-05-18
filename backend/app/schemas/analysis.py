from pydantic import BaseModel, Field


class StartAnalysisRequest(BaseModel):
    project_id: str
    source_id: int | str
    subset_size: int = Field(default=32, gt=0)
    step_size: int = Field(default=8, gt=0)
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


class AnalysisResultsResponse(BaseModel):
    curva_desplaz_carga: dict
    curva_esfuerzo_strain: dict
    mapa_xx_url: str
    mapa_yy_url: str
    mapa_xy_url: str
    esfuerzo_max_mpa: float
    strain_max: float
    coef_correlacion_medio: float
