"""
dgai.api.routes.v1 — Agrégation des routes de l'API v1.
"""

from fastapi import APIRouter
from dgai.api.routes.v1.auth import router as auth_router
from dgai.api.routes.v1.system import router as system_router

v1_router = APIRouter()
v1_router.include_router(auth_router)
v1_router.include_router(system_router)

__all__ = ["v1_router"]
