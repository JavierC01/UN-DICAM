from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.device import CameraInfo, OpenDeviceRequest, VideoFrameResponse, VideoSourceResponse
from app.services.devices import DeviceService, DeviceServiceError

router = APIRouter()
device_service = DeviceService()


@router.get("/cameras", response_model=list[CameraInfo])
def list_cameras() -> list[CameraInfo]:
    return device_service.list_cameras()


@router.post("/upload", response_model=VideoSourceResponse, status_code=status.HTTP_201_CREATED)
def upload_video(file: UploadFile = File(...)) -> VideoSourceResponse:
    """Sube un video (archivo del PC o grabado con el celular); su source_id es el nombre guardado en storage/uploads/."""
    try:
        nombre = device_service.save_upload(file.filename, file.file)
        return device_service.open_source(OpenDeviceRequest(type="file", source_id=nombre))
    except DeviceServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    finally:
        file.file.close()


@router.post("/open", response_model=VideoSourceResponse)
def open_device(payload: OpenDeviceRequest) -> VideoSourceResponse:
    try:
        return device_service.open_source(payload)
    except DeviceServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/frame/{source_id}", response_model=VideoFrameResponse)
def get_first_frame(source_id: str) -> VideoFrameResponse:
    try:
        return device_service.get_first_frame(source_id)
    except DeviceServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
