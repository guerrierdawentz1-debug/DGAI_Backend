"""
dgai.reasoning.router — Analyseur d'intention et routeur de modèle (Brain Router).
"""

import re
from typing import List, Optional
from dgai.llm.errors import ModelNotFoundError
from dgai.llm.registry import ModelRegistry, get_model_registry
from dgai.llm.types import ModelCapability, ModelMetadata, ModelStatus
from dgai.reasoning.types import (
    EstimatedComplexity,
    IntentType,
    RequestAnalysis,
)

# Heuristiques de détection d'intention (sans prétendre à une omniscience artificielle)
CODE_PATTERNS = [
    re.compile(r"\b(def|class|function|fonction|import|export|const|let|var|return|async|await)\b", re.IGNORECASE),
    re.compile(r"\b(code|coder|programmer|développer|python|javascript|rust|sql|html|css|api|fibonacci|algorithme)\b", re.IGNORECASE),
    re.compile(r"```[a-z]*\n"),
]

TRANSLATION_PATTERNS = [
    re.compile(r"\b(traduis|traduire|translation|translate)\b", re.IGNORECASE),
    re.compile(r"\b(en\s+(anglais|français|espagnol|allemand|italien))\b", re.IGNORECASE),
]

ANALYSIS_PATTERNS = [
    re.compile(r"\b(résume|synthèse|analyse|résumer|extraire|synthétiser)\b", re.IGNORECASE),
    re.compile(r"\b(document|rapport|texte\s+suivant|pdf|article)\b", re.IGNORECASE),
]

SUPPORT_PATTERNS = [
    re.compile(r"\b(réclamation|aide|problème|support|commande|remboursement|facture|client)\b", re.IGNORECASE),
]

CONTENT_PATTERNS = [
    re.compile(r"\b(rédige|écris|article|poème|histoire|newsletter|blog|slogan)\b", re.IGNORECASE),
]


class IntentAnalyzer:
    """
    Analyseur syntaxique et heuristique préliminaire des demandes utilisateurs.
    """

    @classmethod
    def analyze(cls, text: str, declared_language: Optional[str] = None) -> RequestAnalysis:
        stripped = text.strip()

        # 1. Détection de langue primaire
        lang = declared_language or ("en" if any(w in text.lower() for w in ["the", "this", "please", "write", "code"]) else "fr")

        # 2. Détection d'intention
        intent = IntentType.CONVERSATION
        required_caps = [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT]
        domain = "general"
        complexity = EstimatedComplexity.LOW

        if any(p.search(stripped) for p in CODE_PATTERNS):
            intent = IntentType.CODING
            domain = "programming"
            required_caps.append(ModelCapability.CODE)
            complexity = EstimatedComplexity.MEDIUM

        elif any(p.search(stripped) for p in TRANSLATION_PATTERNS):
            intent = IntentType.TRANSLATION
            domain = "languages"
            required_caps.append(ModelCapability.MULTILINGUAL)

        elif any(p.search(stripped) for p in ANALYSIS_PATTERNS):
            intent = IntentType.DOCUMENT_ANALYSIS
            domain = "analysis"
            required_caps.append(ModelCapability.REASONING)
            complexity = EstimatedComplexity.MEDIUM

        elif any(p.search(stripped) for p in SUPPORT_PATTERNS):
            intent = IntentType.CUSTOMER_SUPPORT
            domain = "support"

        elif any(p.search(stripped) for p in CONTENT_PATTERNS):
            intent = IntentType.CONTENT_CREATION
            domain = "content"

        if len(stripped) > 1000:
            complexity = EstimatedComplexity.HIGH

        return RequestAnalysis(
            intent=intent,
            language=lang,
            domain=domain,
            required_capabilities=list(set(required_caps)),
            complexity=complexity,
            requires_tools=False
        )


class BrainRouter:
    """
    Routeur de modèle intelligent de DGAI.
    Sélectionne le meilleur modèle dans le registre selon les capacités requises et la disponibilité.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self._registry = registry or get_model_registry()

    def select_model(self, analysis: RequestAnalysis) -> ModelMetadata:
        """
        Sélectionne un modèle opérationnel répondant aux exigences de l'analyse.
        Si aucun modèle compatible n'est disponible, lève ModelNotFoundError.
        """
        available_models = [
            m for m in self._registry.list_models()
            if m.status in (ModelStatus.LOADED, ModelStatus.AVAILABLE)
        ]

        if not available_models:
            raise ModelNotFoundError("Aucun modèle n'est actuellement disponible ou chargé dans le registre.")

        # Filtrage par capacités requises
        compatible = []
        for model in available_models:
            has_all_caps = all(cap in model.capabilities for cap in analysis.required_capabilities)
            if has_all_caps:
                compatible.append(model)

        # Si aucun modèle n'a toutes les capacités spécialisées, se rabattre sur un modèle généraliste text_generation
        if not compatible:
            compatible = [
                m for m in available_models
                if ModelCapability.TEXT_GENERATION in m.capabilities
            ]

        if not compatible:
            raise ModelNotFoundError(
                f"Aucun modèle compatible avec les capacités requises ({[c.value for c in analysis.required_capabilities]})."
            )

        # Privilégier les modèles déjà chargés en mémoire
        loaded = [m for m in compatible if m.status == ModelStatus.LOADED]
        if loaded:
            return loaded[0]

        return compatible[0]
