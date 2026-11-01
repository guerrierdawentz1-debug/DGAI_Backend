"""
dgai.api.routes.v1.system — Informations sur le système DGAI et statut opérationnel.
"""

import sys
from fastapi import APIRouter, Depends
from dgai.api.dependencies import require_permission
from dgai.api.schemas.common import APIResponse
from dgai.api.schemas.health import SystemInfoResponse
from dgai.core.config import get_settings
from dgai.safety.auth import TokenData
from dgai.safety.permissions import Permission

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/info", response_model=APIResponse[SystemInfoResponse])
async def get_system_info(
    token_data: TokenData = Depends(require_permission(Permission.READ_SYSTEM_INFO))
) -> APIResponse[SystemInfoResponse]:
    """
    Retourne les informations non sensibles du système DGAI.
    Exige une authentification avec permission READ_SYSTEM_INFO.
    """
    settings = get_settings()

    info = SystemInfoResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        api_prefix=settings.api_prefix,
        docs_enabled=settings.enable_docs,
        active_features=[
            "Phase 1: Foundations",
            "Phase 2: Security & API Gateway",
        ],
        rate_limit_per_minute=settings.rate_limit_requests_per_minute
    )

    return APIResponse[SystemInfoResponse](
        success=True,
        message="Informations système récupérées avec succès.",
        data=info
    )
