import hashlib
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.cargas.importador import ImportacionCargaError, extraer_serie, leer_tabla
from app.cargas.sincronizacion import EVENTOS_INICIO
from app.db.models import MachineLoad, Project
from app.db.session import get_db
from app.schemas.loads import MachineLoadResponse

router = APIRouter()

LIMITE_ARCHIVO_BYTES = 20 * 1024 * 1024


def _respuesta(stored: MachineLoad, columnas: list[str]) -> MachineLoadResponse:
    return MachineLoadResponse(
        configurado=True,
        columnas=columnas,
        nombre_archivo=stored.nombre_archivo,
        n_puntos=len(stored.tiempos_s),
        duracion_s=stored.tiempos_s[-1] - stored.tiempos_s[0],
        carga_max_n=max(stored.cargas_n),
        filas_descartadas=stored.filas_descartadas,
        mapeo=stored.mapeo,
        sincronizacion=stored.sincronizacion,
    )


@router.post("/{project_id}/archivo", response_model=MachineLoadResponse)
def import_machine_file(
    project_id: UUID,
    file: UploadFile = File(...),
    columna_tiempo: str | None = Form(None),
    columna_carga: str | None = Form(None),
    unidad_tiempo: str = Form("s"),
    unidad_carga: str = Form("N"),
    offset_s: float = Form(0.0),
    evento_inicio: str = Form("ninguno"),
    umbral_n: float | None = Form(None),
    db: Session = Depends(get_db),
) -> MachineLoadResponse:
    """Importa el CSV/XLSX de la maquina. Sin columnas elegidas solo devuelve las columnas del archivo (configurado=false)."""
    if db.get(Project, str(project_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    contenido = file.file.read(LIMITE_ARCHIVO_BYTES + 1)
    if len(contenido) > LIMITE_ARCHIVO_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo de carga supera 20 MB")
    try:
        tabla = leer_tabla(contenido, file.filename or "")
        columnas = list(tabla.columns)
        if not columna_tiempo or not columna_carga:
            return MachineLoadResponse(configurado=False, columnas=columnas)
        if evento_inicio not in EVENTOS_INICIO:
            raise ImportacionCargaError(f"evento_inicio debe ser uno de: {', '.join(EVENTOS_INICIO)}")
        if evento_inicio == "umbral_carga" and umbral_n is None:
            raise ImportacionCargaError("El evento 'umbral_carga' necesita umbral_n")
        tiempos, cargas, descartadas = extraer_serie(tabla, columna_tiempo, columna_carga, unidad_tiempo, unidad_carga)
    except ImportacionCargaError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stored = db.get(MachineLoad, str(project_id))
    if stored is None:
        stored = MachineLoad(project_id=str(project_id))
        db.add(stored)
    stored.nombre_archivo = file.filename or "carga"
    stored.sha256 = hashlib.sha256(contenido).hexdigest()
    stored.mapeo = {
        "columna_tiempo": columna_tiempo,
        "columna_carga": columna_carga,
        "unidad_tiempo": unidad_tiempo,
        "unidad_carga": unidad_carga,
    }
    stored.sincronizacion = {"offset_s": offset_s, "evento_inicio": evento_inicio, "umbral_n": umbral_n}
    stored.tiempos_s = tiempos
    stored.cargas_n = cargas
    stored.filas_descartadas = descartadas
    db.commit()
    return _respuesta(stored, columnas)


@router.get("/{project_id}", response_model=MachineLoadResponse)
def get_machine_load(project_id: UUID, db: Session = Depends(get_db)) -> MachineLoadResponse:
    stored = db.get(MachineLoad, str(project_id))
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se ha importado archivo de carga")
    return _respuesta(stored, [stored.mapeo["columna_tiempo"], stored.mapeo["columna_carga"]])
