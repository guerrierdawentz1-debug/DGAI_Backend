"""
dgai.api.schemas.common — Modèles Pydantic pour les requêtes et réponses communes.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Enveloppe standardisée de réponse DGAI."""
    success: bool = Field(default=True, description="Indicateur de succès de la requête")
    message: Optional[str] = Field(default=None, description="Message descriptif ou d'erreur")
    data: Optional[T] = Field(default=None, description="Données utiles retournées")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Horodatage ISO-8601 UTC de la réponse"
    )


class ErrorDetail(BaseModel):
    """Détail d'une erreur d'API."""
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    """Enveloppe standardisée d'erreur DGAI (évitant la fuite de traces internes)."""
    success: bool = False
    error: str
    details: Optional[List[ErrorDetail]] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TokenResponse(BaseModel):
    """Réponse d'authentification contenant le jeton d'accès JWT."""
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    role: str
