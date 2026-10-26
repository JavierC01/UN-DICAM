import os
import tempfile
from uuid import uuid4

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")
os.environ.setdefault("SECRET_KEY", "clave-solo-para-tests-0123456789abcdef")
os.environ.setdefault("STORAGE_DIR", tempfile.mkdtemp(prefix="undicam-tests-"))

from app.Core.celery_app import celery_app  # noqa: E402
from app.db.init_db import init_db  # noqa: E402

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True
celery_app.conf.task_store_eager_result = True

init_db()


@pytest.fixture
def client():
    """TestClient con sesion iniciada (JWT en el encabezado Authorization)."""
    from fastapi.testclient import TestClient

    from app.main import app

    cliente = TestClient(app)
    correo = f"{uuid4().hex}@test.co"
    cliente.post("/api/v1/auth/register", json={"full_name": "Tester", "email": correo, "password": "secreto123"})
    token = cliente.post("/api/v1/auth/login", json={"email": correo, "password": "secreto123"}).json()["access_token"]
    cliente.headers["Authorization"] = f"Bearer {token}"
    return cliente
