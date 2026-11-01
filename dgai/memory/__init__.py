"""
dgai.memory — Système de mémoire multi-couches de DGAI.
"""

from dgai.memory.conversation import ConversationManager
from dgai.memory.errors import (
    ConversationNotFoundError,
    MemoryError,
    MemoryNotFoundError,
    PrivacyViolationError,
    StorageError,
)
from dgai.memory.long_term import LongTermMemoryManager
from dgai.memory.manager import MemoryManager, get_memory_manager
from dgai.memory.retrieval import MemoryRetriever
from dgai.memory.session import SessionManager
from dgai.memory.storage.base import BaseMemoryStorage
from dgai.memory.storage.sqlite import SQLiteMemoryStorage
from dgai.memory.summarizer import ConversationSummarizer
from dgai.memory.types import (
    ConfidenceLevel,
    Conversation,
    ConversationMessage,
    ConversationSummary,
    LongTermMemory,
    MemoryCategory,
    SessionState,
)

__all__ = [
    "MemoryManager",
    "get_memory_manager",
    "ConversationManager",
    "LongTermMemoryManager",
    "SessionManager",
    "MemoryRetriever",
    "ConversationSummarizer",
    "BaseMemoryStorage",
    "SQLiteMemoryStorage",
    "Conversation",
    "ConversationMessage",
    "LongTermMemory",
    "ConversationSummary",
    "SessionState",
    "MemoryCategory",
    "ConfidenceLevel",
    "MemoryError",
    "ConversationNotFoundError",
    "MemoryNotFoundError",
    "StorageError",
    "PrivacyViolationError",
]
