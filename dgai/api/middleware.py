"""
dgai.api.middleware — Middlewares de sécurité pour FastAPI.

- Limitation de la taille du corps de requête (Max Body Size).
- Application du Rate Limiting par IP client.
- En-têtes de sécurité HTTP (X-Content-Type-Options, X-Frame-Options, HSTS).
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from dgai.api.exceptions import PayloadTooLargeException, RateLimitExceededException
from dgai.core.config import get_settings
from dgai.safety.rate_limit import get_rate_limiter


import uuid

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injecte les en-têtes de sécurité recommandés par l'OWASP et l'identifiant de corrélation."""
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extraire ou générer le Correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Correlation-ID"] = correlation_id
        return response


from fastapi.responses import JSONResponse
from dgai.api.schemas.common import ErrorDetail, ErrorResponse
from dgai.safety.audit import SecurityEventType, log_security_event


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Rejette immédiatement les requêtes dont le corps excède la limite configurée."""
    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        content_length = request.headers.get("content-length")

        if content_length:
            try:
                length_int = int(content_length)
                if length_int > settings.max_request_size_bytes:
                    client_ip = request.client.host if request.client else "unknown"
                    log_security_event(
                        event_type=SecurityEventType.PAYLOAD_TOO_LARGE,
                        client_ip=client_ip,
                        endpoint=request.url.path,
                        details={"content_length": length_int, "max_allowed": settings.max_request_size_bytes}
                    )
                    content = ErrorResponse(
                        error=f"Le corps de la requête ({length_int} octets) excède la limite maximale autorisée ({settings.max_request_size_bytes} octets).",
                        details=[ErrorDetail(code="PAYLOAD_TOO_LARGE", message="Taille maximale dépassée.")]
                    ).model_dump()
                    return JSONResponse(status_code=413, content=content)
            except ValueError:
                pass  # En-tête corrompu, la validation suivante le gèrera

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Applique la limitation de débit par IP client."""
    async def dispatch(self, request: Request, call_next) -> Response:
        # Laisser passer la route de santé sans rate limit strict
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        limiter = get_rate_limiter()

        if not limiter.is_allowed(client_ip):
            log_security_event(
                event_type=SecurityEventType.RATE_LIMIT_EXCEEDED,
                client_ip=client_ip,
                endpoint=request.url.path,
                details={"reason": "Trop de requêtes dans la minute"}
            )
            content = ErrorResponse(
                error="Limite de débit de requêtes dépassée. Veuillez réessayer plus tard.",
                details=[ErrorDetail(code="RATE_LIMIT_EXCEEDED", message="Trop de requêtes.")]
            ).model_dump()
            return JSONResponse(status_code=429, content=content)

        return await call_next(request)
