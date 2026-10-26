from pathlib import Path

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.v1.routes.analysis import ultimo_resultado
from app.Core.config import settings
from app.db.models import Analysis, Project
from app.db.session import get_db
from app.dic.export import exportar_csv, exportar_jpg, exportar_pdf

router = APIRouter()


def _adjunto(contenido: bytes | str, media_type: str, nombre: str) -> Response:
    return Response(content=contenido, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{nombre}"'})


@router.get("/csv/{analysis_id}")
def export_csv(analysis_id: str, db: Session = Depends(get_db)) -> Response:
    data = ultimo_resultado(db, analysis_id).data
    return _adjunto(exportar_csv(data), "text/csv; charset=utf-8", f"undicam_{analysis_id}.csv")


@router.get("/jpg/{analysis_id}")
def export_jpg(analysis_id: str, db: Session = Depends(get_db)) -> Response:
    data = ultimo_resultado(db, analysis_id).data
    return _adjunto(exportar_jpg(data, Path(settings.STORAGE_DIR)), "image/jpeg", f"undicam_{analysis_id}.jpg")


@router.get("/pdf/{analysis_id}")
def export_pdf(analysis_id: str, db: Session = Depends(get_db)) -> Response:
    data = ultimo_resultado(db, analysis_id).data
    project = db.get(Project, db.get(Analysis, analysis_id).project_id)
    nombre = project.name if project else analysis_id
    return _adjunto(exportar_pdf(data, Path(settings.STORAGE_DIR), nombre), "application/pdf", f"undicam_{analysis_id}.pdf")
