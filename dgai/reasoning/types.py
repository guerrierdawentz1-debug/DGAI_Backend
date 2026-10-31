"""
dgai.reasoning.types — Types et structures de données pour l'analyse des requêtes et le routage.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from dgai.llm.types import ModelCapability


class IntentType(str, Enum):
    """Types d'intentions détectables à l'entrée de DGAI."""
    CONVERSATION = "conversation"
    CONTENT_CREATION = "content_creation"
    DOCUMENT_ANALYSIS = "document_analysis"
    CODING = "coding"
    CUSTOMER_SUPPORT = "customer_support"
    TRANSLATION = "translation"
    UNKNOWN = "unknown"


class EstimatedComplexity(str, Enum):
    """Niveau de complexité estimé pour le dimensionnement du calcul."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RequestAnalysis(BaseModel):
    """
    Analyse structurelle et intentionnelle d'une demande utilisateur.
    IMPORTANT : Ce résultat contient des faits et des décisions observables,
    et ne divulgue aucun monologue interne privé.
    """
    intent: IntentType = Field(default=IntentType.CONVERSATION, description="Intention principale identifiée")
    language: str = Field(default="fr", description="Code de langue détecté ou déclaré (ex: 'fr', 'en')")
    domain: str = Field(default="general", description="Domaine d'application identifié")
    required_capabilities: List[ModelCapability] = Field(
        default_factory=lambda: [ModelCapability.TEXT_GENERATION],
        description="Capacités techniques exigées du modèle"
    )
    complexity: EstimatedComplexity = Field(
        default=EstimatedComplexity.LOW,
        description="Complexité estimée"
    )
    requires_tools: bool = Field(
        default=False,
        description="Indique si la requête nécessitera l'appel d'un outil externe ultérieur"
    )
