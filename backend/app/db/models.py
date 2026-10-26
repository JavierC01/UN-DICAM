from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
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
    tracking_mesh: Mapped["TrackingMesh | None"] = relationship(back_populates="project", cascade="all, delete-orphan")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    machine_load: Mapped["MachineLoad | None"] = relationship(back_populates="project", cascade="all, delete-orphan")


class SpecimenConfig(Base):
    __tablename__ = "specimen_config"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), primary_key=True)
    long_calibracion_px: Mapped[float] = mapped_column(Float, nullable=False)
    long_calibracion_mm: Mapped[float] = mapped_column(Float, nullable=False)
    ancho_mm: Mapped[float] = mapped_column(Float, nullable=False)
    espesor_mm: Mapped[float] = mapped_column(Float, nullable=False)
    long_calibre_mm: Mapped[float] = mapped_column(Float, nullable=False)
    roi_carga: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Fase 7. Columnas agregadas sin migracion: ver "Cambios de esquema" en el README.
    tipo_ensayo: Mapped[str] = mapped_column(String(30), nullable=False, default="traccion", server_default="traccion")
    parametros_ensayo: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    fuente_carga: Mapped[str] = mapped_column(String(20), nullable=False, default="ninguna", server_default="ninguna")
    px_por_mm: Mapped[float] = mapped_column(Float, nullable=False)
    mm_por_px: Mapped[float] = mapped_column(Float, nullable=False)
    area_mm2: Mapped[float] = mapped_column(Float, nullable=False)

    project: Mapped[Project] = relationship(back_populates="specimen_config")


class TrackingMesh(Base):
    __tablename__ = "tracking_meshes"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), primary_key=True)
    frame_width: Mapped[int] = mapped_column(Integer, nullable=False)
    frame_height: Mapped[int] = mapped_column(Integer, nullable=False)
    poligono: Mapped[list] = mapped_column(JSON, nullable=False)
    nodos: Mapped[list] = mapped_column(JSON, nullable=False)
    filas: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    columnas: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    area_px: Mapped[float] = mapped_column(Float, nullable=False)
    validos: Mapped[list | None] = mapped_column(JSON, nullable=True)
    subset_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    puntos_ensayo: Mapped[list | None] = mapped_column(JSON, nullable=True)

    project: Mapped[Project] = relationship(back_populates="tracking_mesh")


class MachineLoad(Base):
    """Serie de carga importada del archivo de la maquina, ya convertida a segundos y newton."""

    __tablename__ = "machine_loads"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), primary_key=True)
    nombre_archivo: Mapped[str] = mapped_column(String(255), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mapeo: Mapped[dict] = mapped_column(JSON, nullable=False)
    sincronizacion: Mapped[dict] = mapped_column(JSON, nullable=False)
    tiempos_s: Mapped[list] = mapped_column(JSON, nullable=False)
    cargas_n: Mapped[list] = mapped_column(JSON, nullable=False)
    filas_descartadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    project: Mapped[Project] = relationship(back_populates="machine_load")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.utcnow, nullable=True)

    project: Mapped[Project] = relationship(back_populates="analyses")
    results: Mapped[list["Result"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(String(80), ForeignKey("analyses.id"), nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)

    analysis: Mapped[Analysis] = relationship(back_populates="results")
