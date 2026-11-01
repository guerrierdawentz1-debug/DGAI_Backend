"""
dgai.api.routes.v1 — Agrégation des routes de l'API v1.
"""

from fastapi import APIRouter
from dgai.api.routes.v1.auth import router as auth_router
from dgai.api.routes.v1.chat import router as chat_router
from dgai.api.routes.v1.conversations import router as conversations_router
from dgai.api.routes.v1.memories import router as memories_router
from dgai.api.routes.v1.system import router as system_router

v1_router = APIRouter()
v1_router.include_router(auth_router)
v1_router.include_router(system_router)
v1_router.include_router(chat_router)
v1_router.include_router(conversations_router)
v1_router.include_router(memories_router)

__all__ = ["v1_router"]
