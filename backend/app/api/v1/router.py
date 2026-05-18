from fastapi import APIRouter

from app.api.v1.routes import analysis, devices, exports, projects, specimen, tracking

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
api_router.include_router(tracking.router, prefix="/tracking", tags=["Tracking"])
api_router.include_router(specimen.router, prefix="/specimen", tags=["Specimen"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(exports.router, prefix="/export", tags=["Export"])
