from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from app.schemas.analysis import AnalysisResultsResponse, AnalysisStatusResponse, StartAnalysisRequest, StartAnalysisResponse
from app.workers.tasks import dummy_task, process_full_analysis

router = APIRouter()


@router.post("/start", response_model=StartAnalysisResponse)
def start_analysis(payload: StartAnalysisRequest) -> StartAnalysisResponse:
    task = process_full_analysis.delay(payload.project_id, str(payload.source_id), payload.model_dump())
    return StartAnalysisResponse(task_id=task.id, status="pending")


@router.post("/dummy", response_model=StartAnalysisResponse)
def start_dummy_task() -> StartAnalysisResponse:
    task = dummy_task.delay()
    return StartAnalysisResponse(task_id=task.id, status="pending")


@router.get("/status/{task_id}", response_model=AnalysisStatusResponse)
def get_status(task_id: str) -> AnalysisStatusResponse:
    task = process_full_analysis.AsyncResult(task_id)
    meta = task.info if isinstance(task.info, dict) else {}
    return AnalysisStatusResponse(
        task_id=task_id,
        status=task.status.lower(),
        progress=int(meta.get("progress", 100 if task.successful() else 0)),
        frames_procesados=int(meta.get("frames_procesados", 0)),
        frames_total=int(meta.get("frames_total", 0)),
        mensaje=str(meta.get("mensaje", task.status)),
    )


@router.get("/results/{analysis_id}", response_model=AnalysisResultsResponse)
def get_results(analysis_id: str) -> AnalysisResultsResponse:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Resultados del analisis {analysis_id} pendientes de implementar en la Fase 4.",
    )


@router.delete("/{analysis_id}", status_code=status.HTTP_202_ACCEPTED)
def cancel_analysis(analysis_id: str) -> dict[str, str]:
    process_full_analysis.AsyncResult(analysis_id).revoke(terminate=True)
    return {"status": "cancel_requested", "analysis_id": analysis_id}


@router.websocket("/ws/{task_id}")
async def analysis_ws(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    try:
        await websocket.send_json({"task_id": task_id, "status": "connected"})
        await websocket.close()
    except WebSocketDisconnect:
        return
