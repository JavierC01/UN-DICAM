import os

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("CELERY_BROKER_URL", "memory://")
os.environ.setdefault("CELERY_RESULT_BACKEND", "cache+memory://")

from app.Core.celery_app import celery_app  # noqa: E402
from app.db.init_db import init_db  # noqa: E402

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True
celery_app.conf.task_store_eager_result = True

init_db()
