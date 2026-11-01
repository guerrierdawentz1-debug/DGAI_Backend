"""
Tests pour le résumeur automatique de conversations (dgai.memory.summarizer).
"""

import pytest
from dgai.llm.engine import LLMEngine
from dgai.llm.providers.mock import MockModelProvider
from dgai.llm.registry import ModelRegistry
from dgai.llm.types import ExecutionEngine, ModelCapability, ModelMetadata
from dgai.memory.storage.sqlite import SQLiteMemoryStorage
from dgai.memory.summarizer import ConversationSummarizer
from dgai.memory.types import ConversationMessage, ConversationSummary


@pytest.mark.asyncio
async def test_summarizer_with_mock_provider():
    """Vérifie le déclenchement du résumé avec le mock provider en environnement de test."""
    storage = SQLiteMemoryStorage(":memory:")
    registry = ModelRegistry()
    engine = LLMEngine(registry=registry)

    mock_provider = MockModelProvider(simulate_latency_seconds=0.01)
    engine.register_provider(mock_provider)

    model = ModelMetadata(
        model_id="summary-model-test",
        name="Summary Model",
        family="Mock",
        engine=ExecutionEngine.MOCK,
        capabilities=[ModelCapability.TEXT_GENERATION],
        is_mock=True
    )
    registry.register_model(model)
    await engine.load_model("summary-model-test")

    summarizer = ConversationSummarizer(storage, engine)

    from dgai.memory.types import Conversation
    # Créer la conversation parente pour respecter la contrainte de clé étrangère
    storage.save_conversation(Conversation(id="c-sum", user_id="u1", title="Conversation Test"))

    # Créer 15 messages pour dépasser le seuil d'auto-résumé (12)
    messages = [
        ConversationMessage(id=f"m-{i}", conversation_id="c-sum", user_id="u1", role="user" if i % 2 == 0 else "assistant", content=f"Échange d'idées numéro {i}")
        for i in range(15)
    ]

    res = await summarizer.summarize_conversation("u1", "c-sum", messages, model_id="summary-model-test")
    assert res is not None
    assert "[MOCK_TEST_RESPONSE" in res.summary
    assert res.conversation_id == "c-sum"


@pytest.mark.asyncio
async def test_summarizer_unavailable_model_preserves_existing():
    """Vérifie que l'indisponibilité du modèle n'écrase pas un ancien résumé valide."""
    storage = SQLiteMemoryStorage(":memory:")
    registry = ModelRegistry()
    engine = LLMEngine(registry=registry)  # Aucun modèle chargé

    from dgai.memory.types import Conversation
    # Créer la conversation parente pour respecter la contrainte de clé étrangère
    storage.save_conversation(Conversation(id="c-safe", user_id="u1", title="Conversation Safe"))

    # Ancien résumé valide pré-existant
    old_summary = ConversationSummary(
        conversation_id="c-safe",
        user_id="u1",
        summary="Ancien résumé intègre conservé."
    )
    storage.save_summary(old_summary)

    summarizer = ConversationSummarizer(storage, engine)
    messages = [
        ConversationMessage(id=f"m-{i}", conversation_id="c-safe", user_id="u1", role="user", content=f"Msg {i}")
        for i in range(15)
    ]

    res = await summarizer.summarize_conversation("u1", "c-safe", messages, model_id="modele_inexistant")
    assert res is not None
    assert res.summary == "Ancien résumé intègre conservé."  # Non écrasé
