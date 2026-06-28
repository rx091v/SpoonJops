from fastapi import APIRouter

from backend.app.api.routes import dashboard, system

api_router = APIRouter()
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
