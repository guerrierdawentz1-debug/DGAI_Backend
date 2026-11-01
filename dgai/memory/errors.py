"""
dgai.memory.errors — Exceptions du système de mémoire.
"""


class MemoryError(Exception):
    """Exception de base pour les erreurs de mémoire."""
    def __init__(self, message: str, code: str = "MEMORY_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ConversationNotFoundError(MemoryError):
    """Levée quand une conversation demandée n'existe pas ou n'appartient pas à l'utilisateur."""
    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Conversation introuvable : '{conversation_id}'.",
            code="CONVERSATION_NOT_FOUND"
        )
        self.conversation_id = conversation_id


class MemoryNotFoundError(MemoryError):
    """Levée quand un souvenir demandé n'existe pas ou n'appartient pas à l'utilisateur."""
    def __init__(self, memory_id: str):
        super().__init__(
            message=f"Souvenir introuvable : '{memory_id}'.",
            code="MEMORY_NOT_FOUND"
        )
        self.memory_id = memory_id


class StorageError(MemoryError):
    """Levée lors d'un échec technique de stockage (I/O, intégrité, corruption)."""
    def __init__(self, message: str):
        super().__init__(
            message=f"Erreur de stockage mémoire : {message}",
            code="STORAGE_ERROR"
        )


class PrivacyViolationError(MemoryError):
    """Levée lorsqu'une tentative de mémorisation viole les politiques de confidentialité (secret, PII)."""
    def __init__(self, message: str):
        super().__init__(
            message=f"Violation de la politique de confidentialité : {message}",
            code="PRIVACY_VIOLATION"
        )
