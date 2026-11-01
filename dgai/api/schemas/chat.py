"""
dgai.api.schemas.chat — Schémas Pydantic pour la route de chat d'inférence.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Message au format conversationnel."""
    role: str = Field(pattern=r"^(user|assistant|system)$", description="Rôle de l'émetteur")
    content: str = Field(min_length=1, max_length=65536, description="Contenu du message")


class ChatRequest(BaseModel):
    """Requête de chat transmise à l'endpoint /api/v1/chat."""
    messages: List[ChatMessage] = Field(min_length=1, description="Historique ou liste des messages")
    conversation_id: Optional[str] = Field(default=None, description="Identifiant d'une conversation persistée existante")
    model_id: Optional[str] = Field(default=None, description="Modèle souhaité (optionnel, sélectionné par BrainRouter si omis)")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Température")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=8192, description="Tokens max")


class ChatChoice(BaseModel):
    """Choix de réponse généré."""
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatResponse(BaseModel):
    """Réponse normalisée de chat."""
    id: str
    model_id: str
    engine: str
    choices: List[ChatChoice]
    usage: dict
    latency_seconds: float
    is_mock: bool = False
