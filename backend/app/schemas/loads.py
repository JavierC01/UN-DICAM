from pydantic import BaseModel


class MachineLoadResponse(BaseModel):
    configurado: bool
    columnas: list[str]
    nombre_archivo: str | None = None
    n_puntos: int | None = None
    duracion_s: float | None = None
    carga_max_n: float | None = None
    filas_descartadas: int | None = None
    mapeo: dict | None = None
    sincronizacion: dict | None = None
