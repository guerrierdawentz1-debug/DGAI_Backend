"""
dgai.llm — Moteur d'inférence, Registre des modèles et Fournisseurs de DGAI.
"""

from dgai.llm.engine import LLMEngine, get_llm_engine
from dgai.llm.errors import (
    ConcurrencyLimitExceededError,
    LLMError,
    ModelExecutionError,
    ModelNotFoundError,
    ModelNotLoadedError,
    ModelTimeoutError,
)
from dgai.llm.registry import ModelRegistry, get_model_registry
from dgai.llm.types import (
    ExecutionEngine,
    GenerationParams,
    GenerationRequest,
    GenerationResponse,
    ModelCapability,
    ModelMetadata,
    ModelStatus,
    TokenUsage,
)

__all__ = [
    "LLMEngine",
    "get_llm_engine",
    "ModelRegistry",
    "get_model_registry",
    "ExecutionEngine",
    "ModelCapability",
    "ModelStatus",
    "ModelMetadata",
    "GenerationParams",
    "GenerationRequest",
    "GenerationResponse",
    "TokenUsage",
    "LLMError",
    "ModelNotFoundError",
    "ModelNotLoadedError",
    "ModelExecutionError",
    "ModelTimeoutError",
    "ConcurrencyLimitExceededError",
]
