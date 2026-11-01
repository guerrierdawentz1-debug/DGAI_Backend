"""
dgai.reasoning — Analyse des requêtes, Compréhension des intentions et Brain Router.
"""

from dgai.reasoning.context import ContextAssemblyResult, ContextManager, estimate_tokens
from dgai.reasoning.router import BrainRouter, IntentAnalyzer
from dgai.reasoning.types import (
    EstimatedComplexity,
    IntentType,
    RequestAnalysis,
)

__all__ = [
    "BrainRouter",
    "IntentAnalyzer",
    "IntentType",
    "EstimatedComplexity",
    "RequestAnalysis",
    "ContextManager",
    "ContextAssemblyResult",
    "estimate_tokens",
]
