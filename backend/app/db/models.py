from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    specimen_config: Mapped["SpecimenConfig | None"] = relationship(back_populates="project", cascade="all, delete-orphan")


class SpecimenConfig(Base):
    __tablename__ = "specimen_config"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), primary_key=True)
    long_calibracion_px: Mapped[float] = mapped_column(Float, nullable=False)
    long_calibracion_mm: Mapped[float] = mapped_column(Float, nullable=False)
    ancho_mm: Mapped[float] = mapped_column(Float, nullable=False)
    espesor_mm: Mapped[float] = mapped_column(Float, nullable=False)
    long_calibre_mm: Mapped[float] = mapped_column(Float, nullable=False)
    roi_carga: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    px_por_mm: Mapped[float] = mapped_column(Float, nullable=False)
    mm_por_px: Mapped[float] = mapped_column(Float, nullable=False)
    area_mm2: Mapped[float] = mapped_column(Float, nullable=False)

    project: Mapped[Project] = relationship(back_populates="specimen_config")


class ImagePair(Base):
    __tablename__ = "image_pairs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    reference_path: Mapped[str] = mapped_column(Text, nullable=False)
    deformed_path: Mapped[str] = mapped_column(Text, nullable=False)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(String(80), ForeignKey("analyses.id"), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
