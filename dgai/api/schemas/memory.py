"""
dgai.api.schemas.memory — Schémas Pydantic pour les routes de conversations et mémoires.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from dgai.memory.types import ConfidenceLevel, MemoryCategory


class CreateConversationRequest(BaseModel):
    """Demande de création d'une nouvelle conversation."""
    title: Optional[str] = Field(default=None, max_length=128, description="Titre optionnel")


class ConversationResponse(BaseModel):
    """Détail d'une conversation."""
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageResponse(BaseModel):
    """Message d'une conversation."""
    id: str
    conversation_id: str
    user_id: str
    role: str
    content: str
    created_at: str


class CreateMemoryRequest(BaseModel):
    """Demande de mémorisation à long terme."""
    content: str = Field(min_length=1, max_length=10000, description="Fait ou préférence à mémoriser")
    category: MemoryCategory = Field(default=MemoryCategory.EXPLICIT_NOTE, description="Catégorie")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.HIGH, description="Niveau de confiance")
    source_conversation_id: Optional[str] = Field(default=None, description="Conversation d'origine")
    retention_days: Optional[int] = Field(default=None, ge=1, le=3650, description="Durée de rétention en jours")


class UpdateMemoryRequest(BaseModel):
    """Mise à jour d'un souvenir existant."""
    content: Optional[str] = Field(default=None, min_length=1, max_length=10000)
    category: Optional[MemoryCategory] = None
    confidence: Optional[ConfidenceLevel] = None


class MemoryResponse(BaseModel):
    """Détail d'un souvenir durable."""
    id: str
    user_id: str
    category: MemoryCategory
    content: str
    confidence: ConfidenceLevel
    source_conversation_id: Optional[str]
    created_at: str
    updated_at: str
    expires_at: Optional[str]
