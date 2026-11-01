"""
dgai.memory.long_term — Gestionnaire de la mémoire persistante à long terme (Long-Term Memory).
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from dgai.core.config import get_settings
from dgai.memory.errors import MemoryNotFoundError, PrivacyViolationError
from dgai.memory.policies.privacy import validate_memory_privacy
from dgai.memory.policies.retention import compute_expiration_date
from dgai.memory.storage.base import BaseMemoryStorage
from dgai.memory.types import ConfidenceLevel, LongTermMemory, MemoryCategory


class LongTermMemoryManager:
    """
    Gère la persistance, la validation, la mise à jour et la suppression des souvenirs durables.
    Applique la politique de confidentialité avant tout enregistrement.
    """

    def __init__(self, storage: BaseMemoryStorage):
        self._storage = storage
        self._settings = get_settings()

    def add_memory(
        self,
        user_id: str,
        content: str,
        category: MemoryCategory = MemoryCategory.EXPLICIT_NOTE,
        confidence: ConfidenceLevel = ConfidenceLevel.HIGH,
        source_conversation_id: Optional[str] = None,
        retention_days: Optional[int] = None
    ) -> LongTermMemory:
        """
        Valide et enregistre un souvenir durable.
        Rejette le contenu si la mémoire à long terme est désactivée ou s'il contient des secrets.
        """
        if not self._settings.long_term_memory_enabled:
            raise PrivacyViolationError("La mémoire à long terme est actuellement désactivée par configuration.")

        # 1. Validation de confidentialité (interdiction des secrets / PII)
        validate_memory_privacy(content)

        # 2. Vérification de longueur
        if len(content) > self._settings.max_memory_content_chars:
            raise ValueError(
                f"Le contenu dépasse la taille maximale autorisée ({self._settings.max_memory_content_chars} caractères)."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        expires_at = compute_expiration_date(retention_days)

        memory = LongTermMemory(
            id=f"mem-{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            category=category,
            content=content.strip(),
            confidence=confidence,
            source_conversation_id=source_conversation_id,
            created_at=now_iso,
            updated_at=now_iso,
            expires_at=expires_at,
            is_deleted=False
        )

        return self._storage.save_long_term_memory(memory)

    def get_memory(self, user_id: str, memory_id: str) -> LongTermMemory:
        """Récupère un souvenir par identifiant. Lève MemoryNotFoundError si absent ou autre propriétaire."""
        memory = self._storage.get_long_term_memory(user_id, memory_id)
        if not memory:
            raise MemoryNotFoundError(memory_id)
        return memory

    def list_memories(
        self,
        user_id: str,
        category: Optional[MemoryCategory] = None,
        include_expired: bool = False
    ) -> List[LongTermMemory]:
        """Liste les souvenirs actifs d'un utilisateur."""
        cat_str = category.value if category else None
        return self._storage.list_long_term_memories(user_id, category=cat_str, include_expired=include_expired)

    def update_memory(
        self,
        user_id: str,
        memory_id: str,
        content: Optional[str] = None,
        confidence: Optional[ConfidenceLevel] = None,
        category: Optional[MemoryCategory] = None
    ) -> LongTermMemory:
        """Met à jour un souvenir existant."""
        existing = self.get_memory(user_id, memory_id)

        new_content = existing.content
        if content is not None:
            validate_memory_privacy(content)
            if len(content) > self._settings.max_memory_content_chars:
                raise ValueError("Contenu trop long.")
            new_content = content.strip()

        updated = existing.model_copy(update={
            "content": new_content,
            "confidence": confidence or existing.confidence,
            "category": category or existing.category,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })

        return self._storage.save_long_term_memory(updated)

    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Supprime définitivement un souvenir."""
        # Vérifier d'abord l'existence et l'appartenance
        self.get_memory(user_id, memory_id)
        return self._storage.delete_long_term_memory(user_id, memory_id)

    def purge_user_memories(self, user_id: str) -> int:
        """Supprime tous les souvenirs d'un utilisateur (droit à l'oubli)."""
        return self._storage.delete_all_user_memories(user_id)
