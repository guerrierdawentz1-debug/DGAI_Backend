"""
dgai.api.schemas.health — Modèles Pydantic pour les routes de santé et d'information système.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """État de santé global du service DGAI."""
    status: str = Field(default="healthy", description="État de santé général ('healthy', 'degraded')")
    app_name: str
    version: str
    environment: str
    timestamp: str


class SystemInfoResponse(BaseModel):
    """Informations système publiques et non sensibles."""
    app_name: str
    version: str
    environment: str
    python_version: str
    api_prefix: str
    docs_enabled: bool
    active_features: List[str]
    rate_limit_per_minute: int
