"""
dgai.api.schemas — Point d'accès aux modèles d'API.
"""

from dgai.api.schemas.common import APIResponse, ErrorDetail, ErrorResponse, TokenResponse
from dgai.api.schemas.health import HealthResponse, SystemInfoResponse

__all__ = [
    "APIResponse",
    "ErrorDetail",
    "ErrorResponse",
    "TokenResponse",
    "HealthResponse",
    "SystemInfoResponse",
]
