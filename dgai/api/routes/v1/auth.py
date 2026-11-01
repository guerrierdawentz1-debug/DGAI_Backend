"""
dgai.api.routes.v1.auth — Routes d'authentification et de délivrance de jetons.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from dgai.api.schemas.common import APIResponse, TokenResponse
from dgai.core.config import get_settings
from dgai.safety.auth import create_access_token
from dgai.safety.permissions import Role

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenRequest(BaseModel):
    """Demande de jeton (identifiant client ou rôle)."""
    client_id: str = Field(min_length=3, max_length=64, description="Identifiant unique du client")
    requested_role: Role = Field(default=Role.USER, description="Rôle demandé (par défaut USER)")


@router.post("/token", response_model=APIResponse[TokenResponse])
async def issue_token(body: TokenRequest) -> APIResponse[TokenResponse]:
    """
    Génère un jeton JWT d'accès pour interagir avec les endpoints protégés.
    Le rôle ADMIN ne peut pas être auto-attribué anonymement.
    """
    if body.requested_role == Role.ADMIN and body.client_id != "dgai-admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Attribution du rôle ADMIN non autorisée pour ce client."
        )

    settings = get_settings()
    token = create_access_token(
        subject=body.client_id,
        role=body.requested_role
    )

    data = TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.jwt_access_token_expire_minutes,
        role=body.requested_role.value
    )

    return APIResponse[TokenResponse](
        success=True,
        message="Jeton généré avec succès.",
        data=data
    )
