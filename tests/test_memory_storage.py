"""
Tests unitaires pour la couche de stockage SQLite (dgai.memory.storage.sqlite).
"""

import pytest
from dgai.memory.storage.sqlite import SQLiteMemoryStorage
from dgai.memory.types import (
    ConfidenceLevel,
    Conversation,
    ConversationMessage,
    ConversationSummary,
    LongTermMemory,
    MemoryCategory,
    SessionState,
)


@pytest.fixture
def memory_storage():
    return SQLiteMemoryStorage(":memory:")


def test_conversation_lifecycle_and_cascade_delete(memory_storage):
    """Vérifie la création, récupération et cascade delete d'une conversation."""
    conv = Conversation(id="conv-1", user_id="user-a", title="Test Cascade")
    memory_storage.save_conversation(conv)

    msg1 = ConversationMessage(id="msg-1", conversation_id="conv-1", user_id="user-a", role="user", content="Hello")
    msg2 = ConversationMessage(id="msg-2", conversation_id="conv-1", user_id="user-a", role="assistant", content="Hi")
    memory_storage.save_message(msg1)
    memory_storage.save_message(msg2)

    summary = ConversationSummary(conversation_id="conv-1", user_id="user-a", summary="Test summary")
    memory_storage.save_summary(summary)

    # Récupération vérifiée
    assert memory_storage.get_conversation("user-a", "conv-1") is not None
    messages = memory_storage.get_messages("user-a", "conv-1")
    assert len(messages) == 2
    assert memory_storage.get_summary("user-a", "conv-1") is not None

    # Suppression en cascade
    deleted = memory_storage.delete_conversation("user-a", "conv-1")
    assert deleted is True
    assert memory_storage.get_conversation("user-a", "conv-1") is None
    assert len(memory_storage.get_messages("user-a", "conv-1")) == 0
    assert memory_storage.get_summary("user-a", "conv-1") is None


def test_long_term_memory_storage(memory_storage):
    """Vérifie le stockage, la mise à jour et la suppression des mémoires durables."""
    mem = LongTermMemory(
        id="mem-1",
        user_id="user-a",
        category=MemoryCategory.USER_PREFERENCE,
        content="Préfère le mode sombre",
        confidence=ConfidenceLevel.VERIFIED
    )
    memory_storage.save_long_term_memory(mem)

    retrieved = memory_storage.get_long_term_memory("user-a", "mem-1")
    assert retrieved is not None
    assert retrieved.content == "Préfère le mode sombre"
    assert retrieved.confidence == ConfidenceLevel.VERIFIED

    # Mise à jour
    updated_mem = retrieved.model_copy(update={"content": "Préfère le mode clair"})
    memory_storage.save_long_term_memory(updated_mem)
    assert memory_storage.get_long_term_memory("user-a", "mem-1").content == "Préfère le mode clair"

    # Suppression physique
    assert memory_storage.delete_long_term_memory("user-a", "mem-1") is True
    assert memory_storage.get_long_term_memory("user-a", "mem-1") is None


def test_session_state_storage(memory_storage):
    """Vérifie la persistance et mise à jour de la mémoire de travail (SessionState)."""
    conv = Conversation(id="conv-sess", user_id="user-a", title="Session test")
    memory_storage.save_conversation(conv)

    state = SessionState(
        conversation_id="conv-sess",
        user_id="user-a",
        current_topic="Base de données",
        goals=["Optimiser les requêtes"],
        decisions=["Utiliser SQLite"],
        open_tasks=["Créer index"]
    )
    memory_storage.save_session_state(state)

    fetched = memory_storage.get_session_state("user-a", "conv-sess")
    assert fetched is not None
    assert fetched.current_topic == "Base de données"
    assert len(fetched.goals) == 1
    assert len(fetched.decisions) == 1
