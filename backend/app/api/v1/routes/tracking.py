from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import TrackingMesh
from app.db.session import get_db
from app.schemas.tracking import MeshRequest, MeshResponse, TrackingValidationResponse
from app.services.tracking import TrackingService, TrackingServiceError

router = APIRouter()
tracking_service = TrackingService()


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
    stored.area_px = mesh.area_px

    db.commit()
    return mesh


@router.post("/validate", response_model=TrackingValidationResponse)
def validate_polygon(payload: MeshRequest) -> TrackingValidationResponse:
    return tracking_service.validate(payload)
