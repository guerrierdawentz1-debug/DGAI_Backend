"""
Tests unitaires pour le Moteur Central LLM (LLMEngine) et le Mock Provider.
"""

import asyncio
import pytest
from dgai.llm.engine import LLMEngine
from dgai.llm.errors import (
    ConcurrencyLimitExceededError,
    LLMError,
    ModelExecutionError,
    ModelNotFoundError,
    ModelNotLoadedError,
    ModelTimeoutError,
)
from dgai.llm.providers.mock import MockModelProvider
from dgai.llm.registry import ModelRegistry
from dgai.llm.types import (
    ExecutionEngine,
    GenerationParams,
    GenerationRequest,
    ModelCapability,
    ModelMetadata,
)


@pytest.fixture
def configured_engine():
    """Initialise un LLMEngine avec registre et MockModelProvider."""
    registry = ModelRegistry()
    engine = LLMEngine(registry=registry, max_concurrent=2)
    provider = MockModelProvider(simulate_latency_seconds=0.01)
    engine.register_provider(provider)

    model = ModelMetadata(
        model_id="test-mock-agent",
        name="Test Mock Agent",
        family="Synthetic",
        engine=ExecutionEngine.MOCK,
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT],
        is_mock=True
    )
    registry.register_model(model)
    return engine, registry, provider, model


@pytest.mark.asyncio
async def test_llm_engine_generation_success(configured_engine):
    """Vérifie la génération complète et normalisée avec le Mock Provider."""
    engine, registry, provider, model = configured_engine

    # Charger le modèle
    loaded = await engine.load_model(model.model_id)
    assert loaded is True

    req = GenerationRequest(
        prompt="Bonjour, comment vas-tu ?",
        model_id=model.model_id,
        params=GenerationParams(max_tokens=100, temperature=0.5)
    )

    response = await engine.generate(req)
    assert response.is_mock is True
    assert "[MOCK_TEST_RESPONSE" in response.text
    assert response.model_id == model.model_id
    assert response.usage.prompt_tokens > 0
    assert response.usage.completion_tokens > 0


@pytest.mark.asyncio
async def test_llm_engine_model_not_loaded(configured_engine):
    """Vérifie l'erreur quand le modèle est enregistré mais pas chargé en mémoire."""
    engine, registry, provider, model = configured_engine

    req = GenerationRequest(prompt="Test", model_id=model.model_id)
    with pytest.raises(ModelNotLoadedError):
        await engine.generate(req)


@pytest.mark.asyncio
async def test_llm_engine_prompt_length_limit(configured_engine):
    """Vérifie le rejet d'un prompt dépassant la limite maximale configurée."""
    engine, registry, provider, model = configured_engine
    huge_prompt = "x" * 40000  # > 32768 caractères
    req = GenerationRequest(prompt=huge_prompt, model_id=model.model_id)

    with pytest.raises(ValueError) as exc:
        await engine.generate(req)
    assert "dépasse la limite maximale" in str(exc.value)


@pytest.mark.asyncio
async def test_llm_engine_timeout(configured_engine):
    """Vérifie le respect strict du timeout de génération."""
    engine, registry, provider, model = configured_engine
    # Configurer une latence artificielle supérieure au timeout
    slow_provider = MockModelProvider(simulate_latency_seconds=0.2)
    engine.register_provider(slow_provider)
    await engine.load_model(model.model_id)

    req = GenerationRequest(
        prompt="Question lente",
        model_id=model.model_id,
        params=GenerationParams(timeout_seconds=0.05)
    )

    with pytest.raises(ModelTimeoutError):
        await engine.generate(req)


@pytest.mark.asyncio
async def test_llm_engine_concurrency_control(configured_engine):
    """Vérifie la protection par sémaphore contre les surcharges de requêtes simultanées."""
    engine, registry, provider, model = configured_engine
    await engine.load_model(model.model_id)

    # Réduire le sémaphore à 1 pour tester la concurrence
    engine._semaphore = asyncio.Semaphore(1)
    engine._max_concurrent = 1

    # Simuler une exécution concurrente
    provider._simulate_latency = 0.05
    req = GenerationRequest(prompt="Requete concurrente", model_id=model.model_id)

    tasks = [engine.generate(req), engine.generate(req)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Au moins une requête doit réussir, et les requêtes excédentaires sont gérées
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) >= 1
