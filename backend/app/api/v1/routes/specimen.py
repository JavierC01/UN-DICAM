from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import SpecimenConfig
from app.db.session import get_db
from app.schemas.specimen import SpecimenConfigRequest, SpecimenConfigResponse
from app.services.specimen import SpecimenService, SpecimenServiceError

router = APIRouter()
specimen_service = SpecimenService()


@router.post("/configure", response_model=SpecimenConfigResponse)
def configure_specimen(payload: SpecimenConfigRequest, db: Session = Depends(get_db)) -> SpecimenConfigResponse:
    try:
        response = specimen_service.configure(payload)
    except SpecimenServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    stored = db.get(SpecimenConfig, payload.project_id)
    if stored is None:
        stored = SpecimenConfig(project_id=payload.project_id)
        db.add(stored)

    stored.long_calibracion_px = payload.long_calibracion_px
    stored.long_calibracion_mm = payload.long_calibracion_mm
    stored.ancho_mm = payload.ancho_mm
    stored.espesor_mm = payload.espesor_mm
    stored.long_calibre_mm = payload.long_calibre_mm
    stored.roi_carga = payload.roi_carga
    stored.px_por_mm = response.px_por_mm
    stored.mm_por_px = response.mm_por_px
    stored.area_mm2 = response.area_mm2

    db.commit()
    return response


@router.get("/{project_id}", response_model=SpecimenConfigResponse)
def get_specimen(project_id: UUID, db: Session = Depends(get_db)) -> SpecimenConfigResponse:
    stored = db.get(SpecimenConfig, str(project_id))
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuracion de probeta no encontrada")
    return SpecimenConfigResponse(
        px_por_mm=stored.px_por_mm,
        mm_por_px=stored.mm_por_px,
        area_mm2=stored.area_mm2,
        confirmado=True,
    )
