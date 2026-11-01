"""
dgai.memory.types — Modèles de données typés pour le système de mémoire multi-couches.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MemoryCategory(str, Enum):
    """Catégories de mémoires à long terme autorisées."""
    USER_PREFERENCE = "user_preference"
    PROJECT_INFO = "project_info"
    FACT = "fact"
    INSTRUCTION = "instruction"
    EXPLICIT_NOTE = "explicit_note"


class ConfidenceLevel(str, Enum):
    """Niveau de certitude de la mémoire stockée."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERIFIED = "verified"


class ConversationMessage(BaseModel):
    """Message d'une conversation (Short-Term Memory)."""
    id: str = Field(description="Identifiant unique du message")
    conversation_id: str = Field(description="Identifiant de la conversation rattachée")
    user_id: str = Field(description="Propriétaire du message (isolation stricte)")
    role: str = Field(pattern=r"^(user|assistant|system)$", description="Rôle émetteur")
    content: str = Field(min_length=1, description="Contenu textuel du message")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Horodatage ISO-8601 UTC de création"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées non sensibles")


class Conversation(BaseModel):
    """Conversation active ou archivée."""
    id: str = Field(description="Identifiant unique de la conversation")
    user_id: str = Field(description="Propriétaire de la conversation (isolation stricte)")
    title: str = Field(default="Nouvelle conversation", description="Titre de la conversation")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LongTermMemory(BaseModel):
    """Souvenir persistant inter-conversations (Long-Term Memory)."""
    id: str = Field(description="Identifiant unique du souvenir")
    user_id: str = Field(description="Propriétaire du souvenir (isolation stricte)")
    category: MemoryCategory = Field(default=MemoryCategory.EXPLICIT_NOTE, description="Catégorie")
    content: str = Field(min_length=1, max_length=10000, description="Contenu mémorisé")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.HIGH, description="Niveau de confiance")
    source_conversation_id: Optional[str] = Field(default=None, description="Origine conversationnelle éventuelle")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = Field(default=None, description="Date d'expiration facultative ISO-8601 UTC")
    is_deleted: bool = Field(default=False, description="Marqueur de suppression logique")


class ConversationSummary(BaseModel):
    """Résumé structuré d'une conversation longue."""
    conversation_id: str
    user_id: str
    summary: str = Field(description="Résumé global synthétique")
    main_topics: List[str] = Field(default_factory=list, description="Thèmes principaux abordés")
    important_facts: List[str] = Field(default_factory=list, description="Faits marquants")
    decisions: List[str] = Field(default_factory=list, description="Décisions actées")
    open_tasks: List[str] = Field(default_factory=list, description="Tâches pendantes ou ouvertes")
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SessionState(BaseModel):
    """État de session temporaire (Working Memory) rattaché à une conversation."""
    conversation_id: str
    user_id: str
    current_topic: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    open_tasks: List[str] = Field(default_factory=list)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
