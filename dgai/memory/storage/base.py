"""
dgai.memory.storage.base — Interface abstraite pour les adaptateurs de stockage de mémoire.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dgai.memory.types import (
    Conversation,
    ConversationMessage,
    ConversationSummary,
    LongTermMemory,
    SessionState,
)


class BaseMemoryStorage(ABC):
    """
    Interface abstraite pour la persistance des conversations et des mémoires.
    Permet d'interchanger SQLite, PostgreSQL ou un stockage In-Memory sans altérer la logique métier.
    Toutes les opérations appliquent obligatoirement l'isolation par user_id.
    """

    @abstractmethod
    def save_conversation(self, conversation: Conversation) -> Conversation:
        """Crée ou met à jour les métadonnées d'une conversation."""
        pass

    @abstractmethod
    def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Conversation]:
        """Récupère une conversation appartenant strictement à user_id."""
        pass

    @abstractmethod
    def list_conversations(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Conversation]:
        """Liste les conversations d'un utilisateur par ordre antéchronologique."""
        pass

    @abstractmethod
    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """Supprime définitivement une conversation et tous ses messages/résumés associés."""
        pass

    @abstractmethod
    def save_message(self, message: ConversationMessage) -> ConversationMessage:
        """Enregistre un nouveau message dans une conversation."""
        pass

    @abstractmethod
    def get_messages(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 50,
        before_id: Optional[str] = None
    ) -> List[ConversationMessage]:
        """Récupère les messages d'une conversation par ordre chronologique."""
        pass

    @abstractmethod
    def save_long_term_memory(self, memory: LongTermMemory) -> LongTermMemory:
        """Crée ou met à jour une mémoire à long terme."""
        pass

    @abstractmethod
    def get_long_term_memory(self, user_id: str, memory_id: str) -> Optional[LongTermMemory]:
        """Récupère un souvenir par son identifiant unique pour l'utilisateur."""
        pass

    @abstractmethod
    def list_long_term_memories(
        self,
        user_id: str,
        category: Optional[str] = None,
        include_expired: bool = False
    ) -> List[LongTermMemory]:
        """Liste les mémoires d'un utilisateur avec filtres optionnels."""
        pass

    @abstractmethod
    def delete_long_term_memory(self, user_id: str, memory_id: str) -> bool:
        """Supprime définitivement un souvenir de l'utilisateur."""
        pass

    @abstractmethod
    def delete_all_user_memories(self, user_id: str) -> int:
        """Supprime l'intégralité des mémoires durables d'un utilisateur (droit à l'oubli RGPD)."""
        pass

    @abstractmethod
    def save_summary(self, summary: ConversationSummary) -> ConversationSummary:
        """Sauvegarde ou actualise le résumé structuré d'une conversation."""
        pass

    @abstractmethod
    def get_summary(self, user_id: str, conversation_id: str) -> Optional[ConversationSummary]:
        """Récupère le résumé structuré d'une conversation."""
        pass

    @abstractmethod
    def save_session_state(self, state: SessionState) -> SessionState:
        """Sauvegarde ou met à jour l'état de session temporaire."""
        pass

    @abstractmethod
    def get_session_state(self, user_id: str, conversation_id: str) -> Optional[SessionState]:
        """Récupère l'état de session temporaire."""
        pass
