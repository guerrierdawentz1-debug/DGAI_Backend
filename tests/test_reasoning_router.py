"""
Tests unitaires pour l'analyse des requêtes et le Brain Router (dgai.reasoning).
"""

import pytest
from dgai.llm.errors import ModelNotFoundError
from dgai.llm.registry import ModelRegistry
from dgai.llm.types import ExecutionEngine, ModelCapability, ModelMetadata, ModelStatus
from dgai.reasoning.router import BrainRouter, IntentAnalyzer
from dgai.reasoning.types import EstimatedComplexity, IntentType


def test_intent_analyzer_coding():
    """Vérifie la détection d'une intention de programmation."""
    analysis = IntentAnalyzer.analyze("Écris une fonction python def tri_rapide(liste) pour ordonner des entiers.")
    assert analysis.intent == IntentType.CODING
    assert ModelCapability.CODE in analysis.required_capabilities
    assert analysis.domain == "programming"


def test_intent_analyzer_translation():
    """Vérifie la détection d'une intention de traduction."""
    analysis = IntentAnalyzer.analyze("Peux-tu traduire ce paragraphe en anglais s'il te plaît ?")
    assert analysis.intent == IntentType.TRANSLATION
    assert ModelCapability.MULTILINGUAL in analysis.required_capabilities
    assert analysis.domain == "languages"


def test_intent_analyzer_document_analysis():
    """Vérifie la détection d'une intention d'analyse/synthèse documentaire."""
    analysis = IntentAnalyzer.analyze("Fais une synthèse et analyse les points clés de ce rapport de réunion.")
    assert analysis.intent == IntentType.DOCUMENT_ANALYSIS
    assert ModelCapability.REASONING in analysis.required_capabilities


def test_brain_router_selection_by_capabilities():
    """Vérifie que le BrainRouter sélectionne le modèle adapté aux capacités requises."""
    registry = ModelRegistry()

    general_model = ModelMetadata(
        model_id="general-llm",
        name="General LLM",
        family="Test",
        engine=ExecutionEngine.MOCK,
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT],
        is_mock=True
    )
    code_model = ModelMetadata(
        model_id="coder-llm",
        name="Coder LLM",
        family="Test",
        engine=ExecutionEngine.MOCK,
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.CODE],
        is_mock=True
    )

    registry.register_model(general_model)
    registry.register_model(code_model)

    router = BrainRouter(registry)

    # Requête de code
    code_analysis = IntentAnalyzer.analyze("def solve(): pass en python")
    chosen = router.select_model(code_analysis)
    assert chosen.model_id == "coder-llm"


def test_brain_router_no_available_models():
    """Vérifie le rejet propre si aucun modèle n'est enregistré dans le registre."""
    empty_registry = ModelRegistry()
    router = BrainRouter(empty_registry)
    analysis = IntentAnalyzer.analyze("Bonjour")

    with pytest.raises(ModelNotFoundError):
        router.select_model(analysis)
