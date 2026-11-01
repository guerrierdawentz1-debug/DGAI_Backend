"""
dgai.memory.manager — Façade unifiée du système de mémoire de DGAI.
"""

from typing import Optional
from dgai.core.config import get_settings
from dgai.llm.engine import LLMEngine, get_llm_engine
from dgai.memory.conversation import ConversationManager
from dgai.memory.long_term import LongTermMemoryManager
from dgai.memory.retrieval import MemoryRetriever
from dgai.memory.session import SessionManager
from dgai.memory.storage.base import BaseMemoryStorage
from dgai.memory.storage.sqlite import SQLiteMemoryStorage
from dgai.memory.summarizer import ConversationSummarizer


class MemoryManager:
    """
    Point d'entrée unifié orchestrant les 4 couches de mémoire de DGAI :
    - Short-Term Memory (ConversationManager)
    - Long-Term Memory (LongTermMemoryManager)
    - Working Memory (SessionManager)
    - Conversation Summarizer & Retrieval
    """

    def __init__(
        self,
        storage: Optional[BaseMemoryStorage] = None,
        llm_engine: Optional[LLMEngine] = None
    ):
        settings = get_settings()
        self.storage = storage or SQLiteMemoryStorage(settings.sqlite_memory_db_path)
        self.llm_engine = llm_engine or get_llm_engine()

        self.conversations = ConversationManager(self.storage)
        self.long_term = LongTermMemoryManager(self.storage)
        self.sessions = SessionManager(self.storage)
        self.retriever = MemoryRetriever(self.storage)
        self.summarizer = ConversationSummarizer(self.storage, self.llm_engine)


# Instance globale partagée
_memory_manager_instance: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance
