import time

from app.Core.celery_app import celery_app


@celery_app.task(bind=True)
def dummy_task(self) -> dict[str, str]:
    for step in range(1, 6):
        self.update_state(
            state="PROGRESS",
            meta={
                "progress": step * 20,
                "frames_procesados": step,
                "frames_total": 5,
                "mensaje": f"Worker activo: paso {step}/5",
            },
        )
        time.sleep(0.2)
    return {"status": "done"}


@celery_app.task(bind=True)
def process_full_analysis(self, project_id: str, source_id: str, params: dict) -> dict[str, str]:
    self.update_state(
        state="PROGRESS",
        meta={"progress": 1, "frames_procesados": 0, "frames_total": 0, "mensaje": "Pipeline DIC pendiente de Fase 4"},
    )
    return {"status": "queued_placeholder", "project_id": project_id, "source_id": source_id}
