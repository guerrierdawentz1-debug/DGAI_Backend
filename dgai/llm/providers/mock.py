"""
dgai.llm.providers.mock — Fournisseur Mock strictement réservé aux tests unitaires et d'intégration.

IMPORTANT : Ce simulateur déterministe ne constitue en aucun cas une véritable IA.
Toutes ses réponses sont explicitement identifiées par le préfixe '[MOCK_TEST_RESPONSE]'
et le flag 'is_mock = True' pour prévenir toute confusion.
"""

import asyncio
import time
from typing import Dict, Set
from dgai.llm.errors import ModelExecutionError, ModelNotLoadedError, ModelTimeoutError
from dgai.llm.providers.base import BaseModelProvider
from dgai.llm.types import (
    ExecutionEngine,
    GenerationRequest,
    GenerationResponse,
    ModelMetadata,
    TokenUsage,
)


class MockModelProvider(BaseModelProvider):
    """
    Implémentation de test permettant de simuler chargement, latence, génération,
    timeouts et erreurs sans consommer de ressources GPU ni prétendre être un vrai LLM.
    """

    def __init__(self, simulate_latency_seconds: float = 0.01):
        self._simulate_latency = simulate_latency_seconds
        self._loaded_models: Set[str] = set()
        self._fail_on_model_ids: Set[str] = set()

    @property
    def engine(self) -> ExecutionEngine:
        return ExecutionEngine.MOCK

    def set_failing_model(self, model_id: str) -> None:
        """Configure un modèle pour simuler une défaillance d'exécution."""
        self._fail_on_model_ids.add(model_id)

    async def load_model(self, metadata: ModelMetadata) -> bool:
        if not metadata.is_mock:
            # Sécurité : le MockProvider ne doit charger que des modèles typés Mock
            raise ValueError(f"Le MockModelProvider ne peut charger que des modèles marqués is_mock=True : '{metadata.model_id}'")
        self._loaded_models.add(metadata.model_id)
        return True

    async def unload_model(self, model_id: str) -> bool:
        if model_id in self._loaded_models:
            self._loaded_models.remove(model_id)
            return True
        return False

    async def is_ready(self, model_id: str) -> bool:
        return model_id in self._loaded_models

    async def generate(
        self,
        request: GenerationRequest,
        metadata: ModelMetadata
    ) -> GenerationResponse:
        start_time = time.time()

        if metadata.model_id not in self._loaded_models:
            raise ModelNotLoadedError(metadata.model_id)

        if metadata.model_id in self._fail_on_model_ids:
            raise ModelExecutionError("Échec technique simulé du modèle mock.", model_id=metadata.model_id)

        # Simulation de timeout si configuré
        timeout = request.params.timeout_seconds or 30.0
        if self._simulate_latency > timeout:
            await asyncio.sleep(timeout)
            raise ModelTimeoutError(timeout, model_id=metadata.model_id)

        if self._simulate_latency > 0:
            await asyncio.sleep(self._simulate_latency)

        prompt_len = len(request.prompt)
        simulated_tokens = max(1, prompt_len // 4)

        # Construction d'une réponse de test explicite
        simulated_text = (
            f"[MOCK_TEST_RESPONSE:{metadata.model_id}] Réponse simulée pour test pour la requête : "
            f"'{request.prompt[:50]}...'"
        )
        completion_tokens = max(1, len(simulated_text) // 4)

        elapsed = time.time() - start_time

        return GenerationResponse(
            text=simulated_text,
            model_id=metadata.model_id,
            engine=ExecutionEngine.MOCK,
            usage=TokenUsage(
                prompt_tokens=simulated_tokens,
                completion_tokens=completion_tokens,
                total_tokens=simulated_tokens + completion_tokens
            ),
            finish_reason="stop",
            latency_seconds=round(elapsed, 4),
            is_mock=True
        )
