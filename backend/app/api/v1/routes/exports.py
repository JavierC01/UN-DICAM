from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.get("/csv/{analysis_id}")
def export_csv(analysis_id: str) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Exportacion CSV planeada para la Fase 5.")


@router.get("/pdf/{analysis_id}")
def export_pdf(analysis_id: str) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Exportacion PDF planeada para la Fase 5.")


@router.get("/jpg/{analysis_id}")
def export_jpg(analysis_id: str) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Exportacion JPG planeada para la Fase 5.")
