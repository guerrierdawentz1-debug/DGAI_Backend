"""
dgai.api.routes.health — Point de terminaison de vérification de l'état de santé.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from dgai.api.schemas.health import HealthResponse
from dgai.core.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def check_health() -> HealthResponse:
    """
    Vérifie l'état de fonctionnement du service DGAI.
    Cette route publique n'expose aucun secret ni donnée d'infrastructure sensible.
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
