from fastapi import APIRouter, HTTPException, status

from app.schemas.tracking import MeshRequest, MeshResponse, TrackingValidationResponse
from app.services.tracking import TrackingService, TrackingServiceError

router = APIRouter()
tracking_service = TrackingService()


@router.post("/mesh", response_model=MeshResponse)
def build_mesh(payload: MeshRequest) -> MeshResponse:
    try:
        return tracking_service.build_mesh(payload)
    except TrackingServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/validate", response_model=TrackingValidationResponse)
def validate_polygon(payload: MeshRequest) -> TrackingValidationResponse:
    return tracking_service.validate(payload)
