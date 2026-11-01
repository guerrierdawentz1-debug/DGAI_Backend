"""
Tests unitaires pour la gestion de la mémoire à long terme (dgai.memory.long_term).
"""

import pytest
from dgai.memory.errors import MemoryNotFoundError, PrivacyViolationError
from dgai.memory.long_term import LongTermMemoryManager
from dgai.memory.storage.sqlite import SQLiteMemoryStorage
from dgai.memory.types import ConfidenceLevel, MemoryCategory


@pytest.fixture
def memory_manager():
    storage = SQLiteMemoryStorage(":memory:")
    return LongTermMemoryManager(storage)


def test_add_memory_success(memory_manager):
    """Vérifie l'ajout d'une mémoire valide."""
    mem = memory_manager.add_memory(
        user_id="user-1",
        content="Préfère recevoir les explications sous forme de liste à puces",
        category=MemoryCategory.USER_PREFERENCE,
        confidence=ConfidenceLevel.HIGH
    )
    assert mem.id.startswith("mem-")
    assert mem.user_id == "user-1"
    assert mem.category == MemoryCategory.USER_PREFERENCE


def test_reject_password_in_memory(memory_manager):
    """Vérifie le rejet catégorique d'un mot de passe."""
    with pytest.raises(PrivacyViolationError):
        memory_manager.add_memory("user-1", "Mon mot de passe admin est super_secret_123")


def test_reject_api_key_in_memory(memory_manager):
    """Vérifie le rejet catégorique d'une clé API."""
    with pytest.raises(PrivacyViolationError):
        memory_manager.add_memory("user-1", "Clé d'API : api_key=sk-1234567890abcdef123456")


def test_reject_jwt_in_memory(memory_manager):
    """Vérifie le rejet catégorique d'un jeton JWT."""
    with pytest.raises(PrivacyViolationError):
        memory_manager.add_memory("user-1", "Mon token de connexion eyJhbGciOiJIUzI1Ni.eyJzdWIiOiIxMjM0NTY3ODkw.signature")


def test_update_and_delete_memory(memory_manager):
    """Vérifie la mise à jour et la suppression."""
    mem = memory_manager.add_memory("user-1", "Note initiale")
    updated = memory_manager.update_memory("user-1", mem.id, content="Note modifiée")
    assert updated.content == "Note modifiée"

    deleted = memory_manager.delete_memory("user-1", mem.id)
    assert deleted is True

    with pytest.raises(MemoryNotFoundError):
        memory_manager.get_memory("user-1", mem.id)


def test_purge_user_memories(memory_manager):
    """Vérifie la purge complète des mémoires d'un utilisateur (droit à l'oubli)."""
    memory_manager.add_memory("user-purge", "Fait 1")
    memory_manager.add_memory("user-purge", "Fait 2")
    assert len(memory_manager.list_memories("user-purge")) == 2

    count = memory_manager.purge_user_memories("user-purge")
    assert count == 2
    assert len(memory_manager.list_memories("user-purge")) == 0
