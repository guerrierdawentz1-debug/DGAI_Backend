"""
Tests unitaires pour le Registre des modèles (ModelRegistry).
"""

import pytest
from dgai.llm.errors import ModelNotFoundError
from dgai.llm.registry import ModelRegistry
from dgai.llm.types import ExecutionEngine, ModelCapability, ModelMetadata, ModelStatus


def test_model_registration_and_retrieval():
    """Vérifie l'enregistrement et la récupération d'un modèle avec métadonnées complètes."""
    registry = ModelRegistry()
    meta = ModelMetadata(
        model_id="dgai-test-model-1",
        name="DGAI Test Model",
        family="Test",
        engine=ExecutionEngine.MOCK,
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT],
        supported_languages=["fr", "en"],
        context_window_tokens=4096,
        is_mock=True,
        license="Apache-2.0"
    )

    registered = registry.register_model(meta)
    assert registered.model_id == "dgai-test-model-1"

    fetched = registry.get_model("dgai-test-model-1")
    assert fetched.name == "DGAI Test Model"
    assert fetched.context_window_tokens == 4096
    assert fetched.status == ModelStatus.AVAILABLE


def test_model_not_found():
    """Vérifie la levée d'exception pour un modèle inexistant."""
    registry = ModelRegistry()
    with pytest.raises(ModelNotFoundError):
        registry.get_model("modele_fantome_inconnu")


def test_model_unregistration():
    """Vérifie la suppression d'un modèle du registre."""
    registry = ModelRegistry()
    meta = ModelMetadata(
        model_id="temp-model",
        name="Temp",
        family="Test",
        engine=ExecutionEngine.MOCK,
        is_mock=True
    )
    registry.register_model(meta)
    assert len(registry.list_models()) == 1

    assert registry.unregister_model("temp-model") is True
    assert len(registry.list_models()) == 0
    assert registry.unregister_model("temp-model") is False


def test_find_by_capability():
    """Vérifie le filtrage précis par capacité technique déclarée."""
    registry = ModelRegistry()
    m1 = ModelMetadata(
        model_id="code-model",
        name="Code Model",
        family="Test",
        engine=ExecutionEngine.MOCK,
        capabilities=[ModelCapability.CODE],
        is_mock=True
    )
    m2 = ModelMetadata(
        model_id="chat-model",
        name="Chat Model",
        family="Test",
        engine=ExecutionEngine.MOCK,
        capabilities=[ModelCapability.CHAT],
        is_mock=True
    )
    registry.register_model(m1)
    registry.register_model(m2)

    code_models = registry.find_by_capability(ModelCapability.CODE)
    assert len(code_models) == 1
    assert code_models[0].model_id == "code-model"

    chat_models = registry.find_by_capability(ModelCapability.CHAT)
    assert len(chat_models) == 1
    assert chat_models[0].model_id == "chat-model"


def test_set_model_status():
    """Vérifie la mise à jour du statut opérationnel d'un modèle."""
    registry = ModelRegistry()
    meta = ModelMetadata(
        model_id="status-test",
        name="Status Test",
        family="Test",
        engine=ExecutionEngine.MOCK,
        is_mock=True
    )
    registry.register_model(meta)
    registry.set_status("status-test", ModelStatus.LOADED)
    assert registry.get_model("status-test").status == ModelStatus.LOADED
