"""
dgai.memory.session — Gestionnaire de l'état de session temporaire (Working Memory).
"""

from datetime import datetime, timezone
from typing import List, Optional
from dgai.memory.storage.base import BaseMemoryStorage
from dgai.memory.types import SessionState


class SessionManager:
    """
    Gère l'état temporaire rattaché à une conversation en cours (Working Memory).
    """

    def __init__(self, storage: BaseMemoryStorage):
        self._storage = storage

    def get_or_create_session(self, user_id: str, conversation_id: str) -> SessionState:
        """Récupère l'état de session existant ou en initialise un nouveau."""
        state = self._storage.get_session_state(user_id, conversation_id)
        if not state:
            state = SessionState(
                conversation_id=conversation_id,
                user_id=user_id,
                current_topic=None,
                goals=[],
                decisions=[],
                open_tasks=[],
                updated_at=datetime.now(timezone.utc).isoformat()
            )
            self._storage.save_session_state(state)
        return state

    def update_session(
        self,
        user_id: str,
        conversation_id: str,
        current_topic: Optional[str] = None,
        goals: Optional[List[str]] = None,
        decisions: Optional[List[str]] = None,
        open_tasks: Optional[List[str]] = None
    ) -> SessionState:
        """Met à jour les variables d'état de travail de la session."""
        current = self.get_or_create_session(user_id, conversation_id)

        updated = current.model_copy(update={
            "current_topic": current_topic if current_topic is not None else current.current_topic,
            "goals": goals if goals is not None else current.goals,
            "decisions": decisions if decisions is not None else current.decisions,
            "open_tasks": open_tasks if open_tasks is not None else current.open_tasks,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

        return self._storage.save_session_state(updated)
