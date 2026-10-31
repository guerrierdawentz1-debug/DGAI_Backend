"""
dgai.llm.providers — Modules d'intégration des moteurs d'inférence LLM.
"""

from dgai.llm.providers.base import BaseModelProvider
from dgai.llm.providers.mock import MockModelProvider

__all__ = ["BaseModelProvider", "MockModelProvider"]
