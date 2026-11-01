"""
dgai.api.exceptions — Gestion centralisée des exceptions HTTP et sécurité de l'API DGAI.
"""

from typing import List, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dgai.api.schemas.common import ErrorDetail, ErrorResponse
from dgai.safety.audit import SecurityEventType, log_security_event


class DGAIAPIException(Exception):
    """Exception de base pour les erreurs applicatives DGAI."""
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        message: str = "Une erreur interne s'est produite.",
        code: str = "INTERNAL_ERROR",
        details: Optional[List[ErrorDetail]] = None
    ):
        self.status_code = status_code
        self.message = message
        self.code = code
        self.details = details or []
        super().__init__(message)


class AuthenticationException(DGAIAPIException):
    def __init__(self, message: str = "Identifiants ou jeton d'authentification invalide."):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            code="AUTHENTICATION_FAILED"
        )


class PermissionDeniedException(DGAIAPIException):
    def __init__(self, message: str = "Action non autorisée pour ce rôle."):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            code="PERMISSION_DENIED"
        )


class RateLimitExceededException(DGAIAPIException):
    def __init__(self, message: str = "Limite de débit de requêtes dépassée. Veuillez réessayer plus tard."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            code="RATE_LIMIT_EXCEEDED"
        )


class PayloadTooLargeException(DGAIAPIException):
    def __init__(self, message: str = "La taille de la requête dépasse la limite maximale autorisée."):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            message=message,
            code="PAYLOAD_TOO_LARGE"
        )


async def dgai_api_exception_handler(request: Request, exc: DGAIAPIException) -> JSONResponse:
    """Gestionnaire centralisé pour les exceptions applicatives DGAI."""
    client_ip = request.client.host if request.client else "unknown"

    if exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        log_security_event(
            event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
            client_ip=client_ip,
            endpoint=request.url.path,
            details={"error": exc.message}
        )

    response_content = ErrorResponse(
        error=exc.message,
        details=exc.details or [ErrorDetail(code=exc.code, message=exc.message)]
    ).model_dump()

    return JSONResponse(status_code=exc.status_code, content=response_content)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Gestionnaire sécurisé des erreurs de validation Pydantic sans fuite d'informations sensibles."""
    client_ip = request.client.host if request.client else "unknown"

    details = []
    for err in exc.errors():
        field_str = ".".join(str(loc) for loc in err.get("loc", []))
        details.append(ErrorDetail(
            code="VALIDATION_ERROR",
            message=err.get("msg", "Donnée invalide"),
            field=field_str
        ))

    log_security_event(
        event_type=SecurityEventType.VALIDATION_ERROR,
        client_ip=client_ip,
        endpoint=request.url.path,
        details={"validation_errors": [d.message for d in details]}
    )

    response_content = ErrorResponse(
        error="Données de requête invalides ou malformées.",
        details=details
    ).model_dump()

    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=response_content)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Attrape-tout sécurisé : ne divulgue jamais la trace interne (stacktrace) à l'appelant."""
    response_content = ErrorResponse(
        error="Une erreur inattendue est survenue sur le serveur.",
        details=[ErrorDetail(code="INTERNAL_SERVER_ERROR", message="Erreur interne protégée.")]
    ).model_dump()

    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=response_content)
