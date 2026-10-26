from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import SpecimenConfig, TrackingMesh
from app.db.session import get_db
from app.schemas.tracking import MeshRequest, MeshResponse, PuntosEnsayoRequest, TrackingValidationResponse
from app.services.tracking import TrackingService, TrackingServiceError

router = APIRouter()
tracking_service = TrackingService()


def _respuesta(stored: TrackingMesh) -> MeshResponse:
    return MeshResponse(
        nodos=stored.nodos,
        validos=stored.validos or [True] * len(stored.nodos),
        poligono=stored.poligono,
        area_px=stored.area_px,
        filas=stored.filas,
        columnas=stored.columnas,
        subset_size=stored.subset_size or 32,
        puntos_ensayo=stored.puntos_ensayo,
    )


@router.post("/mesh", response_model=MeshResponse)
def build_mesh(payload: MeshRequest, db: Session = Depends(get_db)) -> MeshResponse:
    try:
        mesh = tracking_service.build_mesh(payload)
    except TrackingServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stored = db.get(TrackingMesh, payload.project_id)
    if stored is None:
        stored = TrackingMesh(project_id=payload.project_id)
        db.add(stored)

    stored.frame_width = payload.frame_width
    stored.frame_height = payload.frame_height
    stored.poligono = [p.model_dump() for p in mesh.poligono]
    stored.nodos = [p.model_dump() for p in mesh.nodos]
    stored.validos = mesh.validos
    stored.filas = mesh.filas
    stored.columnas = mesh.columnas
    stored.subset_size = mesh.subset_size
    stored.area_px = mesh.area_px
    stored.puntos_ensayo = None  # la malla cambio: los puntos del extensometro se vuelven a marcar

    db.commit()
    return mesh


@router.put("/{project_id}/puntos-ensayo", response_model=MeshResponse)
def set_test_points(project_id: UUID, payload: PuntosEnsayoRequest, db: Session = Depends(get_db)) -> MeshResponse:
    stored = db.get(TrackingMesh, str(project_id))
    specimen = db.get(SpecimenConfig, str(project_id))
    if stored is None or specimen is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Configura la probeta y construye la malla primero")
    try:
        tracking_service.validate_test_points(
            specimen.tipo_ensayo, payload.puntos, stored.nodos, stored.validos, stored.poligono,
            stored.frame_width, stored.frame_height,
        )
    except TrackingServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    stored.puntos_ensayo = [p.model_dump() for p in payload.puntos]
    db.commit()
    return _respuesta(stored)


@router.post("/validate", response_model=TrackingValidationResponse)
def validate_polygon(payload: MeshRequest) -> TrackingValidationResponse:
    return tracking_service.validate(payload)
