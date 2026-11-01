"""
dgai.memory.conversation — Gestionnaire de l'historique conversationnel (Short-Term Memory).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from dgai.core.config import get_settings
from dgai.memory.errors import ConversationNotFoundError
from dgai.memory.storage.base import BaseMemoryStorage
from dgai.memory.types import Conversation, ConversationMessage


class ConversationManager:
    """
    Gère la création, le chargement, la continuation et l'historique des conversations.
    Applique une isolation stricte par user_id.
    """

    def __init__(self, storage: BaseMemoryStorage):
        self._storage = storage
        self._settings = get_settings()

    def create_conversation(self, user_id: str, title: Optional[str] = None) -> Conversation:
        """Initialise une nouvelle conversation pour l'utilisateur."""
        now_iso = datetime.now(timezone.utc).isoformat()
        conv = Conversation(
            id=f"conv-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            title=title or "Nouvelle conversation",
            created_at=now_iso,
            updated_at=now_iso
        )
        return self._storage.save_conversation(conv)

    def get_conversation(self, user_id: str, conversation_id: str) -> Conversation:
        """Récupère une conversation existante. Lève ConversationNotFoundError si introuvable."""
        conv = self._storage.get_conversation(user_id, conversation_id)
        if not conv:
            raise ConversationNotFoundError(conversation_id)
        return conv

    def list_conversations(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """Liste les conversations de l'utilisateur."""
        return self._storage.list_conversations(user_id, limit=limit, offset=offset)

    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Supprime définitivement une conversation et tout son historique."""
        # Vérifier l'appartenance
        self.get_conversation(user_id, conversation_id)
        return self._storage.delete_conversation(user_id, conversation_id)

    def add_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str
    ) -> ConversationMessage:
        """Ajoute et persiste un message dans la conversation."""
        # Vérifier que la conversation existe et appartient à l'utilisateur
        self.get_conversation(user_id, conversation_id)

        msg = ConversationMessage(
            id=f"msg-{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content.strip(),
            created_at=datetime.now(timezone.utc).isoformat()
        )
        return self._storage.save_message(msg)

    def get_recent_messages(
        self,
        user_id: str,
        conversation_id: str,
        limit: Optional[int] = None
    ) -> List[ConversationMessage]:
        """Récupère les messages récents par ordre chronologique."""
        self.get_conversation(user_id, conversation_id)
        max_limit = limit or self._settings.max_history_messages
        return self._storage.get_messages(user_id, conversation_id, limit=max_limit)
