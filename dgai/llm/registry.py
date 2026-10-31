"""
dgai.llm.registry — Registre central des modèles et gouvernance des métadonnées.
"""

from typing import Dict, List, Optional
from dgai.llm.errors import ModelNotFoundError
from dgai.llm.types import ExecutionEngine, ModelCapability, ModelMetadata, ModelStatus


class ModelRegistry:
    """
    Gestionnaire centralisé des modèles supportés et de leurs caractéristiques réelles.
    Interdit toute attribution arbitraire de capacités non vérifiées.
    """

    def __init__(self):
        self._models: Dict[str, ModelMetadata] = {}

    def register_model(self, metadata: ModelMetadata) -> ModelMetadata:
        """Enregistre ou met à jour les métadonnées d'un modèle."""
        if not metadata.model_id or not metadata.model_id.strip():
            raise ValueError("L'identifiant du modèle 'model_id' ne peut pas être vide.")
        self._models[metadata.model_id] = metadata
        return metadata

    def unregister_model(self, model_id: str) -> bool:
        """Supprime un modèle du registre."""
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False

    def get_model(self, model_id: str) -> ModelMetadata:
        """Récupère un modèle par son identifiant unique. Lève ModelNotFoundError si absent."""
        if model_id not in self._models:
            raise ModelNotFoundError(model_id)
        return self._models[model_id]

    def list_models(self) -> List[ModelMetadata]:
        """Retourne la liste de tous les modèles enregistrés."""
        return list(self._models.values())

    def find_by_capability(self, capability: ModelCapability) -> List[ModelMetadata]:
        """Filtre les modèles possédant une capacité technique donnée."""
        return [m for m in self._models.values() if capability in m.capabilities]

    def find_by_engine(self, engine: ExecutionEngine) -> List[ModelMetadata]:
        """Filtre les modèles nécessitant un moteur d'exécution particulier."""
        return [m for m in self._models.values() if m.engine == engine]

    def set_status(self, model_id: str, status: ModelStatus) -> None:
        """Met à jour le statut opérationnel d'un modèle."""
        model = self.get_model(model_id)
        self._models[model_id] = model.model_copy(update={"status": status})

    def clear(self) -> None:
        """Vide le registre (utile pour les tests isolés)."""
        self._models.clear()


# Instance singleton globale
_model_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    return _model_registry
