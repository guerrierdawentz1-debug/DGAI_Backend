"""
Tests pour les endpoints de santé et les routes d'information système.
"""

import pytest
from fastapi.testclient import TestClient
from dgai.api.app import app
from dgai.safety.auth import create_access_token
from dgai.safety.permissions import Role

client = TestClient(app)


def test_health_check_endpoint():
    """Vérifie la route GET /health sans authentification."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "DGAI Core"
    assert "version" in data
    assert "timestamp" in data


def test_unknown_route_returns_404():
    """Vérifie le comportement d'une route inconnue."""
    response = client.get("/api/v1/non_existent_endpoint")
    assert response.status_code == 404


def test_system_info_requires_auth():
    """Vérifie que /api/v1/system/info rejette les accès sans jeton."""
    response = client.get("/api/v1/system/info")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "authentification" in data["error"].lower()


def test_system_info_with_valid_token():
    """Vérifie que /api/v1/system/info répond avec un jeton valide."""
    token = create_access_token(subject="test_user", role=Role.USER)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/system/info", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["app_name"] == "DGAI Core"
    assert "Phase 1: Foundations" in payload["data"]["active_features"]
    assert "secret_key" not in payload["data"]  # Aucune fuite de secret
