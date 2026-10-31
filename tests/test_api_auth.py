"""
Tests pour l'authentification, les jetons JWT et le contrôle des permissions RBAC.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from dgai.api.app import app
from dgai.safety.auth import create_access_token, decode_access_token
from dgai.safety.permissions import Permission, Role, has_permission

client = TestClient(app)


def test_issue_token_success():
    """Vérifie la génération d'un jeton via la route /api/v1/auth/token."""
    response = client.post(
        "/api/v1/auth/token",
        json={"client_id": "test_app", "requested_role": "user"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["role"] == "user"

    # Vérification du décodage
    decoded = decode_access_token(data["data"]["access_token"])
    assert decoded.sub == "test_app"
    assert decoded.role == Role.USER


def test_admin_role_rejection_for_unauthorized_client():
    """Vérifie qu'un client quelconque ne peut pas réclamer le rôle ADMIN."""
    response = client.post(
        "/api/v1/auth/token",
        json={"client_id": "random_client", "requested_role": "admin"}
    )
    assert response.status_code == 403


def test_expired_token_rejection():
    """Vérifie qu'un jeton expiré est rejeté avec un code HTTP 401."""
    # Créer un jeton émis il y a 200 secondes et expiré il y a 100 secondes (iat < exp < now)
    now_ts = int(datetime.now(timezone.utc).timestamp())
    settings = app.state if hasattr(app, "state") else None
    from dgai.core.config import get_settings
    s = get_settings()
    import jwt
    payload = {"sub": "test_user", "role": "user", "iat": now_ts - 200, "exp": now_ts - 100}
    expired_token = jwt.encode(payload, s.secret_key, algorithm="HS256")

    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/system/info", headers=headers)
    assert response.status_code == 401
    assert "expiré" in response.json()["error"].lower()


def test_invalid_signature_token_rejection():
    """Vérifie qu'un jeton falsifié ou corrompu est rejeté avec un code HTTP 401."""
    tampered_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalidpayload.invalidsignature"
    headers = {"Authorization": f"Bearer {tampered_token}"}
    response = client.get("/api/v1/system/info", headers=headers)
    assert response.status_code == 401


def test_permission_matrix():
    """Vérifie l'attribution correcte des permissions RBAC."""
    assert has_permission(Role.USER, Permission.READ_HEALTH)
    assert has_permission(Role.USER, Permission.READ_SYSTEM_INFO)
    assert not has_permission(Role.USER, Permission.ADMIN_CONFIG)

    assert has_permission(Role.ADMIN, Permission.ADMIN_CONFIG)
    assert has_permission(Role.AGENT, Permission.EXECUTE_TOOL)
    assert not has_permission(Role.ANONYMOUS, Permission.EXECUTE_TOOL)
