"""
dgai.llm.engine — Moteur central LLM de DGAI : orchestration, concurrence et exécution.
"""

import asyncio
from typing import Dict, Optional
from dgai.core.config import get_settings
from dgai.core.logging import get_logger
from dgai.llm.errors import (
    ConcurrencyLimitExceededError,
    LLMError,
    ModelNotFoundError,
    ModelNotLoadedError,
    ModelTimeoutError,
)
from dgai.llm.providers.base import BaseModelProvider
from dgai.llm.registry import ModelRegistry, get_model_registry
from dgai.llm.types import (
    ExecutionEngine,
    GenerationRequest,
    GenerationResponse,
    ModelMetadata,
    ModelStatus,
)

logger = get_logger("llm.engine")


class LLMEngine:
    """
    Chef d'orchestre du moteur d'inférence indépendant de DGAI.
    Gère le cycle de vie des modèles, le contrôle de concurrence, les timeouts
    et la normalisation des réponses vers l'API.
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        max_concurrent: Optional[int] = None
    ):
        self._registry = registry or get_model_registry()
        self._settings = get_settings()
        limit = max_concurrent or self._settings.llm_max_concurrent_requests
        self._semaphore = asyncio.Semaphore(limit)
        self._max_concurrent = limit
        self._providers: Dict[ExecutionEngine, BaseModelProvider] = {}

    def register_provider(self, provider: BaseModelProvider) -> None:
        """Associe une implémentation de provider au moteur d'exécution correspondant."""
        self._providers[provider.engine] = provider
        logger.info(f"Moteur d'inférence enregistré : {provider.engine.value}")

    def get_provider(self, engine: ExecutionEngine) -> Optional[BaseModelProvider]:
        return self._providers.get(engine)

    async def load_model(self, model_id: str) -> bool:
        """Charge un modèle en mémoire via son provider assigné."""
        metadata = self._registry.get_model(model_id)
        provider = self.get_provider(metadata.engine)

        if not provider:
            raise LLMError(f"Aucun provider configuré pour le moteur '{metadata.engine.value}'.")

        self._registry.set_status(model_id, ModelStatus.LOADING)
        try:
            success = await provider.load_model(metadata)
            if success:
                self._registry.set_status(model_id, ModelStatus.LOADED)
                logger.info(f"Modèle chargé avec succès : {model_id} ({metadata.engine.value})")
                return True
            else:
                self._registry.set_status(model_id, ModelStatus.ERROR)
                return False
        except Exception as e:
            self._registry.set_status(model_id, ModelStatus.ERROR)
            logger.error(f"Échec du chargement du modèle {model_id}: {str(e)}")
            raise

    async def unload_model(self, model_id: str) -> bool:
        """Décharge un modèle de la mémoire."""
        metadata = self._registry.get_model(model_id)
        provider = self.get_provider(metadata.engine)

        if not provider:
            return False

        success = await provider.unload_model(model_id)
        if success:
            self._registry.set_status(model_id, ModelStatus.UNLOADED)
            logger.info(f"Modèle déchargé : {model_id}")
        return success

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Exécute la génération de texte avec normalisation, quotas et contrôle strict des erreurs.
        """
        # 1. Validation de la taille du prompt
        if len(request.prompt) > self._settings.max_prompt_length_chars:
            raise ValueError(
                f"Le prompt ({len(request.prompt)} caractères) dépasse la limite maximale "
                f"autorisée ({self._settings.max_prompt_length_chars} caractères)."
            )

        # 2. Identification du modèle cible
        target_model_id = request.model_id or self._settings.default_model_id
        if not target_model_id:
            raise LLMError("Aucun modèle spécifié et aucun modèle par défaut configuré.")

        metadata = self._registry.get_model(target_model_id)

        # 3. Récupération du provider
        provider = self.get_provider(metadata.engine)
        if not provider:
            raise LLMError(f"Aucun provider disponible pour le moteur '{metadata.engine.value}'.")

        # 4. Vérification de vivacité
        if not await provider.is_ready(target_model_id):
            raise ModelNotLoadedError(target_model_id)

        # 5. Application des plafonds de génération
        effective_timeout = request.params.timeout_seconds or self._settings.llm_generation_timeout_seconds
        clamped_tokens = min(request.params.max_tokens, self._settings.max_generation_tokens)
        request.params.max_tokens = clamped_tokens
        request.params.timeout_seconds = effective_timeout

        # 6. Exécution bornée par sémaphore de concurrence et timeout asyncio
        try:
            # Tenter d'acquérir le sémaphore sans blocage indéfini
            acquired = self._semaphore.locked() and self._semaphore._value == 0
            if acquired:
                raise ConcurrencyLimitExceededError(self._max_concurrent)

            async with self._semaphore:
                try:
                    response = await asyncio.wait_for(
                        provider.generate(request, metadata),
                        timeout=effective_timeout
                    )
                    return response
                except asyncio.TimeoutError:
                    raise ModelTimeoutError(effective_timeout, model_id=target_model_id)

        except Exception as e:
            logger.warning(
                f"Erreur d'inférence sur le modèle {target_model_id}: {str(e)}",
                extra={"context": {"model_id": target_model_id, "error_type": type(e).__name__}}
            )
            raise


# Instance globale partagée
_llm_engine_instance: Optional[LLMEngine] = None


def get_llm_engine() -> LLMEngine:
    global _llm_engine_instance
    if _llm_engine_instance is None:
        _llm_engine_instance = LLMEngine()
    return _llm_engine_instance
