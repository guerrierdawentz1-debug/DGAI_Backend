"""
dgai.llm.errors — Hiérarchie d'exceptions typées pour le moteur LLM.
"""


class LLMError(Exception):
    """Exception de base pour les erreurs relatives au moteur LLM."""
    def __init__(self, message: str, code: str = "LLM_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ModelNotFoundError(LLMError):
    """Levée lorsqu'un modèle demandé n'existe pas dans le registre."""
    def __init__(self, model_id: str):
        super().__init__(
            message=f"Modèle introuvable dans le registre : '{model_id}'.",
            code="MODEL_NOT_FOUND"
        )
        self.model_id = model_id


class ModelNotLoadedError(LLMError):
    """Levée lorsqu'un modèle n'est pas encore initialisé ou chargé en mémoire."""
    def __init__(self, model_id: str):
        super().__init__(
            message=f"Le modèle '{model_id}' n'est pas encore chargé en mémoire.",
            code="MODEL_NOT_LOADED"
        )
        self.model_id = model_id


class ModelExecutionError(LLMError):
    """Levée lorsqu'une défaillance technique survient durant l'inférence."""
    def __init__(self, message: str, model_id: str | None = None):
        super().__init__(
            message=f"Erreur d'exécution du modèle : {message}",
            code="MODEL_EXECUTION_ERROR"
        )
        self.model_id = model_id


class ModelTimeoutError(LLMError):
    """Levée lorsqu'une requête de génération dépasse le temps limite alloué."""
    def __init__(self, timeout_seconds: float, model_id: str | None = None):
        super().__init__(
            message=f"Délai d'attente de génération dépassé ({timeout_seconds}s).",
            code="MODEL_TIMEOUT"
        )
        self.timeout_seconds = timeout_seconds
        self.model_id = model_id


class ConcurrencyLimitExceededError(LLMError):
    """Levée lorsque la file d'attente ou la capacité concurrente maximale est atteinte."""
    def __init__(self, max_concurrent: int):
        super().__init__(
            message=f"Capacité de requêtes simultanées atteinte ({max_concurrent}). Veuillez réessayer sous peu.",
            code="CONCURRENCY_LIMIT_EXCEEDED"
        )
        self.max_concurrent = max_concurrent
