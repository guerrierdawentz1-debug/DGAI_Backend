"""
Tests d'isolation stricte entre utilisateurs (User A vs User B).
"""

import pytest
from dgai.memory.errors import ConversationNotFoundError, MemoryNotFoundError
from dgai.memory.manager import MemoryManager
from dgai.memory.storage.sqlite import SQLiteMemoryStorage
from dgai.memory.types import MemoryCategory


@pytest.fixture
def memory_manager():
    storage = SQLiteMemoryStorage(":memory:")
    return MemoryManager(storage=storage)


def test_user_isolation_conversations_and_messages(memory_manager):
    """Vérifie que User A ne peut ni voir, ni modifier, ni supprimer les conversations de User B."""
    conv_b = memory_manager.conversations.create_conversation("user-b", title="Projet Secret B")
    msg_b = memory_manager.conversations.add_message("user-b", conv_b.id, "user", "Message privé B")

    # User A tente de lire la conversation de User B
    with pytest.raises(ConversationNotFoundError):
        memory_manager.conversations.get_conversation("user-a", conv_b.id)

    # User A liste ses conversations (doit être vide)
    convs_a = memory_manager.conversations.list_conversations("user-a")
    assert len(convs_a) == 0

    # User A tente de lire les messages de la conversation de User B
    with pytest.raises(ConversationNotFoundError):
        memory_manager.conversations.get_recent_messages("user-a", conv_b.id)

    # User A tente de supprimer la conversation de User B
    with pytest.raises(ConversationNotFoundError):
        memory_manager.conversations.delete_conversation("user-a", conv_b.id)

    # La conversation de User B existe toujours intacte
    assert memory_manager.conversations.get_conversation("user-b", conv_b.id) is not None


def test_user_isolation_long_term_memories(memory_manager):
    """Vérifie que User A ne peut ni voir, ni modifier, ni supprimer les mémoires de User B."""
    mem_b = memory_manager.long_term.add_memory(
        user_id="user-b",
        content="Préférence confidentielle B",
        category=MemoryCategory.USER_PREFERENCE
    )

    # User A tente d'accéder à la mémoire de B
    with pytest.raises(MemoryNotFoundError):
        memory_manager.long_term.get_memory("user-a", mem_b.id)

    # User A tente de modifier la mémoire de B
    with pytest.raises(MemoryNotFoundError):
        memory_manager.long_term.update_memory("user-a", mem_b.id, content="Tentative d'altération")

    # User A tente de supprimer la mémoire de B
    with pytest.raises(MemoryNotFoundError):
        memory_manager.long_term.delete_memory("user-a", mem_b.id)

    # Recherche isolée : User A ne doit pas récupérer le souvenir de B
    results_a = memory_manager.retriever.retrieve_relevant_memories("user-a", "Préférence confidentielle")
    assert len(results_a) == 0

    results_b = memory_manager.retriever.retrieve_relevant_memories("user-b", "Préférence confidentielle")
    assert len(results_b) == 1
    assert results_b[0].id == mem_b.id
