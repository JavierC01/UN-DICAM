from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.v1.routes import analysis, auth, devices, exports, loads, projects, specimen, tracking

protegido = [Depends(get_current_user)]

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"], dependencies=protegido)
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"], dependencies=protegido)
api_router.include_router(tracking.router, prefix="/tracking", tags=["Tracking"], dependencies=protegido)
api_router.include_router(specimen.router, prefix="/specimen", tags=["Specimen"], dependencies=protegido)
api_router.include_router(loads.router, prefix="/loads", tags=["Loads"], dependencies=protegido)
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"], dependencies=protegido)
api_router.include_router(exports.router, prefix="/export", tags=["Export"], dependencies=protegido)
