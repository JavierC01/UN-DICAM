from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import Analysis, Project
from app.db.session import get_db
from app.schemas.analysis import AnalysisSummary
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(id=str(uuid4()), name=payload.name, status="pending")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: UUID, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, str(project_id))
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    return project


@router.get("/{project_id}/analyses", response_model=list[AnalysisSummary])
def list_project_analyses(project_id: UUID, db: Session = Depends(get_db)) -> list[AnalysisSummary]:
    if db.get(Project, str(project_id)) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    analyses = (
        db.query(Analysis)
        .filter(Analysis.project_id == str(project_id))
        .order_by(Analysis.created_at.desc())
        .all()
    )
    return [
        AnalysisSummary(
            id=a.id,
            project_id=a.project_id,
            status=a.status,
            created_at=a.created_at.isoformat() if a.created_at else None,
            params=a.params,
        )
        for a in analyses
    ]


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, db: Session = Depends(get_db)) -> None:
    project = db.get(Project, str(project_id))
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado")
    db.delete(project)
    db.commit()
