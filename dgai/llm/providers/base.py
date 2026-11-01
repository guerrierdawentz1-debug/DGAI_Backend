"""
dgai.llm.providers.base — Contrat d'interface abstrait pour tous les moteurs d'inférence LLM.
"""

from abc import ABC, abstractmethod
from typing import Optional
from dgai.llm.types import (
    ExecutionEngine,
    GenerationParams,
    GenerationRequest,
    GenerationResponse,
    ModelMetadata,
)


class BaseModelProvider(ABC):
    """
    Interface commune et asynchrone pour les moteurs de modèles.
    Permet de brancher indifféremment Mock, llama.cpp, vLLM ou HuggingFace Transformers.
    """

    @property
    @abstractmethod
    def engine(self) -> ExecutionEngine:
        """Retourne le type de moteur d'exécution."""
        pass

    @abstractmethod
    async def load_model(self, metadata: ModelMetadata) -> bool:
        """Charge les poids d'un modèle en mémoire."""
        pass

    @abstractmethod
    async def unload_model(self, model_id: str) -> bool:
        """Décharge un modèle de la mémoire pour libérer les ressources VRAM/RAM."""
        pass

    @abstractmethod
    async def is_ready(self, model_id: str) -> bool:
        """Vérifie si le modèle spécifié est chargé et opérationnel pour l'inférence."""
        pass

    @abstractmethod
    async def generate(
        self,
        request: GenerationRequest,
        metadata: ModelMetadata
    ) -> GenerationResponse:
        """
        Exécute la génération de texte avec gestion de timeout et retour normalisé.
        """
        pass
