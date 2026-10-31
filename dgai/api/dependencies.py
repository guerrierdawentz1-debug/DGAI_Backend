"""
dgai.api.dependencies — Injections de dépendances pour FastAPI (Auth, Permissions, Audit).
"""

from typing import Optional
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dgai.api.exceptions import AuthenticationException, PermissionDeniedException
from dgai.safety.audit import SecurityEventType, log_security_event
from dgai.safety.auth import TokenData, decode_access_token
from dgai.safety.permissions import Permission, Role, has_permission

security_scheme = HTTPBearer(auto_error=False)


async def get_current_token_data(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> TokenData:
    """
    Extrait et valide le jeton Bearer JWT. Lève AuthenticationException en cas d'échec.
    """
    client_ip = request.client.host if request.client else "unknown"

    if not credentials or not credentials.credentials:
        log_security_event(
            event_type=SecurityEventType.AUTH_FAILURE,
            client_ip=client_ip,
            endpoint=request.url.path,
            details={"reason": "Jeton Bearer absent"}
        )
        raise AuthenticationException("Jeton d'authentification manquant.")

    try:
        token_data = decode_access_token(credentials.credentials)
        log_security_event(
            event_type=SecurityEventType.AUTH_SUCCESS,
            client_ip=client_ip,
            endpoint=request.url.path,
            actor=token_data.sub,
            level="INFO"
        )
        return token_data
    except ValueError as e:
        log_security_event(
            event_type=SecurityEventType.AUTH_FAILURE,
            client_ip=client_ip,
            endpoint=request.url.path,
            details={"reason": str(e)}
        )
        raise AuthenticationException(str(e))


def require_permission(required_perm: Permission):
    """
    Fabrique de dépendance pour exiger une permission RBAC précise.
    """
    async def permission_checker(
        request: Request,
        token_data: TokenData = Depends(get_current_token_data)
    ) -> TokenData:
        client_ip = request.client.host if request.client else "unknown"
        if not has_permission(token_data.role, required_perm):
            log_security_event(
                event_type=SecurityEventType.ACCESS_DENIED,
                client_ip=client_ip,
                endpoint=request.url.path,
                actor=token_data.sub,
                details={"required_permission": required_perm.value, "user_role": token_data.role.value}
            )
            raise PermissionDeniedException(
                f"Permission requise non accordée : '{required_perm.value}'"
            )
        return token_data

    return permission_checker
