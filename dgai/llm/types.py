"""
dgai.llm.types — Structures de données et types typés pour le moteur LLM et le registre.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExecutionEngine(str, Enum):
    """Moteurs d'inférence supportés par l'architecture DGAI."""
    NONE = "none"
    MOCK = "mock"
    LLAMA_CPP = "llama_cpp"
    TRANSFORMERS = "transformers"
    VLLM = "vllm"


class ModelCapability(str, Enum):
    """Capacités fonctionnelles déclarées et vérifiables des modèles."""
    TEXT_GENERATION = "text_generation"
    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    MULTILINGUAL = "multilingual"
    TOOL_CALLING = "tool_calling"


class ModelStatus(str, Enum):
    """Statut de chargement et de vivacité du modèle."""
    UNREGISTERED = "unregistered"
    AVAILABLE = "available"
    LOADING = "loading"
    LOADED = "loaded"
    UNLOADED = "unloaded"
    ERROR = "error"


class ModelMetadata(BaseModel):
    """
    Métadonnées d'un modèle enregistré dans le ModelRegistry.
    Aucune capacité ou performance ne doit être inventée sans mesure réelle.
    """
    model_id: str = Field(description="Identifiant unique du modèle (ex: 'qwen2.5-coder-1.5b-mock')")
    name: str = Field(description="Nom usuel du modèle")
    family: str = Field(description="Famille d'architecture (ex: 'Qwen', 'Mistral', 'Llama', 'Synthetic/Mock')")
    version: str = Field(default="1.0.0", description="Version sémantique du modèle")
    engine: ExecutionEngine = Field(description="Moteur d'exécution requis")
    local_path: Optional[str] = Field(default=None, description="Chemin filesystem vers les poids locaux si présents")
    capabilities: List[ModelCapability] = Field(default_factory=list, description="Liste des capacités attestées")
    supported_languages: List[str] = Field(default_factory=lambda: ["fr", "en"], description="Codes ISO des langues prises en charge")
    context_window_tokens: int = Field(default=2048, ge=128, description="Taille maximale du contexte en tokens")
    required_ram_mb: Optional[int] = Field(default=None, description="Estimation de RAM requise en Mo")
    required_vram_mb: Optional[int] = Field(default=None, description="Estimation de VRAM requise en Mo")
    is_mock: bool = Field(default=False, description="Indicateur explicite si le modèle est un simulateur de test")
    license: str = Field(default="Proprietary/Internal", description="Licence d'utilisation des poids (Apache-2.0, MIT, Llama, etc.)")
    status: ModelStatus = Field(default=ModelStatus.AVAILABLE, description="Statut opérationnel courant")


class GenerationParams(BaseModel):
    """Paramètres configurables pour l'inférence texte."""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Température de sampling")
    max_tokens: int = Field(default=512, ge=1, le=131072, description="Tokens maximum à générer")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling top-p")
    stop_sequences: List[str] = Field(default_factory=list, description="Séquences d'arrêt de génération")
    timeout_seconds: Optional[float] = Field(default=None, ge=0.01, le=600.0, description="Délai maximum par requête")


class GenerationRequest(BaseModel):
    """Requête d'inférence transmise au moteur LLM."""
    prompt: str = Field(min_length=1, description="Texte d'entrée normalisé")
    model_id: Optional[str] = Field(default=None, description="Modèle ciblé (None = auto-sélection par router)")
    params: GenerationParams = Field(default_factory=GenerationParams)
    context_id: Optional[str] = Field(default=None, description="Identifiant contextuel ou de session")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Métadonnées d'accompagnement non sensibles")


class TokenUsage(BaseModel):
    """Comptage des tokens consommés lors de l'inférence."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class GenerationResponse(BaseModel):
    """Réponse structurée et normalisée produite par le moteur LLM."""
    text: str = Field(description="Contenu généré par le modèle")
    model_id: str = Field(description="Modèle exact ayant produit la réponse")
    engine: ExecutionEngine = Field(description="Moteur ayant exécuté la génération")
    usage: TokenUsage = Field(default_factory=TokenUsage, description="Consommation de tokens mesurée")
    finish_reason: str = Field(default="stop", description="Raison d'arrêt ('stop', 'length', 'timeout')")
    latency_seconds: float = Field(ge=0.0, description="Temps total d'exécution de la génération")
    is_mock: bool = Field(default=False, description="Alerte formelle si la réponse émane d'un provider Mock")
