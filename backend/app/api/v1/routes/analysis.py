from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.models import Analysis, Project, Result, SpecimenConfig, TrackingMesh
from app.db.session import get_db
from app.dic.ensayos import ajuste_lineal
from app.schemas.analysis import (
    AjustePropiedadRequest,
    AnalysisResultsResponse,
    AnalysisStatusResponse,
    StartAnalysisRequest,
    StartAnalysisResponse,
)
from app.workers.tasks import dummy_task, process_full_analysis

router = APIRouter()


@router.post("/start", response_model=StartAnalysisResponse)
def start_analysis(payload: StartAnalysisRequest, db: Session = Depends(get_db)) -> StartAnalysisResponse:
    project = db.get(Project, payload.project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    if db.get(SpecimenConfig, payload.project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Calibra la probeta antes de iniciar el analisis"
        )
    if db.get(TrackingMesh, payload.project_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Construye la malla de rastreo antes de iniciar el analisis",
        )

    analysis_id = str(uuid4())
    analysis = Analysis(id=analysis_id, project_id=payload.project_id, task_id=analysis_id, status="pending", params=payload.model_dump())
    db.add(analysis)
    project.status = "in_progress"
    db.commit()

    process_full_analysis.apply_async(
        args=[analysis_id, payload.project_id, payload.source_id, payload.model_dump()],
        task_id=analysis_id,
    )
    return StartAnalysisResponse(task_id=analysis_id, status="pending")


@router.post("/dummy", response_model=StartAnalysisResponse)
def start_dummy_task() -> StartAnalysisResponse:
    task = dummy_task.delay()
    return StartAnalysisResponse(task_id=task.id, status="pending")


@router.get("/status/{task_id}", response_model=AnalysisStatusResponse)
def get_status(task_id: str) -> AnalysisStatusResponse:
    task = process_full_analysis.AsyncResult(task_id)
    meta = task.info if isinstance(task.info, dict) else {}
    return AnalysisStatusResponse(
        task_id=task_id,
        status=task.status.lower(),
        progress=int(meta.get("progress", 100 if task.successful() else 0)),
        frames_procesados=int(meta.get("frames_procesados", 0)),
        frames_total=int(meta.get("frames_total", 0)),
        mensaje=str(meta.get("mensaje", task.status)),
    )


def ultimo_resultado(db: Session, analysis_id: str) -> Result:
    analysis = db.get(Analysis, analysis_id)
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Analisis {analysis_id} no encontrado")
    if analysis.status != "success":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El analisis {analysis_id} todavia no tiene resultados (estado: {analysis.status})",
        )
    result = db.query(Result).filter(Result.analysis_id == analysis_id).order_by(Result.id.desc()).first()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sin resultados para el analisis {analysis_id}")
    return result


@router.get("/results/{analysis_id}", response_model=AnalysisResultsResponse)
def get_results(analysis_id: str, db: Session = Depends(get_db)) -> AnalysisResultsResponse:
    data = ultimo_resultado(db, analysis_id).data
    return AnalysisResultsResponse(
        curva_desplaz_carga=data["curva_desplaz_carga"],
        curva_esfuerzo_strain=data["curva_esfuerzo_strain"],
        ensayo=data.get("ensayo"),
        mapa_xx_url=data["mapa_xx_path"],
        mapa_yy_url=data["mapa_yy_path"],
        mapa_xy_url=data["mapa_xy_path"],
        esfuerzo_max_mpa=data.get("esfuerzo_max_mpa"),
        strain_max=data.get("strain_max"),
        coef_correlacion_medio=data.get("coef_correlacion_medio"),
        carga=data.get("carga", {}),
        advertencias=data.get("advertencias", []),
        metadatos=data.get("metadatos", {}),
    )


@router.post("/{analysis_id}/propiedad")
def fit_property(analysis_id: str, payload: AjustePropiedadRequest, db: Session = Depends(get_db)) -> dict:
    """Ajuste lineal de la curva del ensayo en el rango que elige el usuario (p. ej. el que fija la norma aplicable)."""
    result = ultimo_resultado(db, analysis_id)
    ensayo = result.data.get("ensayo")
    if not ensayo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este analisis no tiene curva del ensayo (faltaron los puntos del extensometro virtual)",
        )
    try:
        ajuste = ajuste_lineal(ensayo["curva"]["x"], ensayo["curva"]["y"], **payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    ajuste["propiedad"] = ensayo["propiedad"]
    ensayo["ajuste"] = ajuste
    flag_modified(result, "data")
    db.commit()
    return ajuste


@router.delete("/{analysis_id}", status_code=status.HTTP_202_ACCEPTED)
def cancel_analysis(analysis_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    process_full_analysis.AsyncResult(analysis_id).revoke(terminate=True)
    analysis = db.get(Analysis, analysis_id)
    if analysis is not None:
        analysis.status = "revoked"
        project = db.get(Project, analysis.project_id)
        if project is not None:
            project.status = "revoked"
        db.commit()
    return {"status": "cancel_requested", "analysis_id": analysis_id}
