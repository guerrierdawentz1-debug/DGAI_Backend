"""
Tests d'intégration des endpoints REST Conversations et Memories.
"""

import pytest
from fastapi.testclient import TestClient
from dgai.api.app import app
from dgai.safety.auth import create_access_token
from dgai.safety.permissions import Role

client = TestClient(app)


def test_conversations_api_crud_and_isolation():
    """Vérifie le cycle complet de gestion des conversations et l'étanchéité inter-utilisateurs."""
    token_a = create_access_token("user_api_a", role=Role.USER)
    token_b = create_access_token("user_api_b", role=Role.USER)
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. User A crée une conversation
    res = client.post("/api/v1/conversations", json={"title": "Projet A"}, headers=headers_a)
    assert res.status_code == 201
    conv_id = res.json()["data"]["id"]

    # 2. User A consulte la conversation
    res_get = client.get(f"/api/v1/conversations/{conv_id}", headers=headers_a)
    assert res_get.status_code == 200
    assert res_get.json()["data"]["title"] == "Projet A"

    # 3. User B tente d'accéder à la conversation de User A -> Doit retourner 404 (sans révéler l'existence)
    res_b_get = client.get(f"/api/v1/conversations/{conv_id}", headers=headers_b)
    assert res_b_get.status_code == 404

    # 4. User B tente de supprimer la conversation de User A -> Doit retourner 404
    res_b_del = client.delete(f"/api/v1/conversations/{conv_id}", headers=headers_b)
    assert res_b_del.status_code == 404

    # 5. User A supprime sa conversation
    res_del = client.delete(f"/api/v1/conversations/{conv_id}", headers=headers_a)
    assert res_del.status_code == 200
    assert client.get(f"/api/v1/conversations/{conv_id}", headers=headers_a).status_code == 404


def test_memories_api_crud_and_privacy_filter():
    """Vérifie la gestion des mémoires à long terme via l'API et le rejet des données sensibles."""
    token = create_access_token("user_mem_test", role=Role.USER)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Rejet d'un mot de passe dans le contenu
    res_bad = client.post(
        "/api/v1/memories",
        json={"content": "Mon mot de passe est password123", "category": "user_preference"},
        headers=headers
    )
    assert res_bad.status_code == 400
    assert "confidentialité" in res_bad.json()["error"].lower()

    # 2. Création d'une mémoire légitime
    res_ok = client.post(
        "/api/v1/memories",
        json={"content": "L'utilisateur préfère le café noir", "category": "user_preference"},
        headers=headers
    )
    assert res_ok.status_code == 201
    mem_id = res_ok.json()["data"]["id"]

    # 3. Consultation
    res_get = client.get(f"/api/v1/memories/{mem_id}", headers=headers)
    assert res_get.status_code == 200
    assert "café noir" in res_get.json()["data"]["content"]

    # 4. Modification
    res_patch = client.patch(
        f"/api/v1/memories/{mem_id}",
        json={"content": "L'utilisateur préfère le thé vert"},
        headers=headers
    )
    assert res_patch.status_code == 200
    assert "thé vert" in res_patch.json()["data"]["content"]

    # 5. Suppression
    res_del = client.delete(f"/api/v1/memories/{mem_id}", headers=headers)
    assert res_del.status_code == 200
    assert client.get(f"/api/v1/memories/{mem_id}", headers=headers).status_code == 404
