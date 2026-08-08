from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.Core.config import settings

_is_sqlite_memory = settings.DATABASE_URL.startswith("sqlite") and ":memory:" in settings.DATABASE_URL

if _is_sqlite_memory:
    # Una sola conexion compartida para que todas las sesiones vean la misma base en memoria
    # (usado en tests; en produccion se usa PostgreSQL).
    engine = create_engine(
        settings.DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
else:
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
