"""
Tests d'intégration de l'endpoint POST /api/v1/chat.
"""

import pytest
from fastapi.testclient import TestClient
from dgai.api.app import app
from dgai.llm.engine import get_llm_engine
from dgai.llm.providers.mock import MockModelProvider
from dgai.llm.types import ExecutionEngine, ModelCapability, ModelMetadata
from dgai.safety.auth import create_access_token
from dgai.safety.permissions import Role

client = TestClient(app)


def test_chat_endpoint_requires_auth():
    """Vérifie le rejet 401 si aucun jeton d'autorisation n'est fourni."""
    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Bonjour"}]}
    )
    assert response.status_code == 401


def test_chat_endpoint_empty_messages():
    """Vérifie le rejet 422 si la liste de messages est vide."""
    token = create_access_token("test_user", role=Role.USER)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/v1/chat", json={"messages": []}, headers=headers)
    assert response.status_code == 422


def test_chat_endpoint_no_model_available():
    """Vérifie le retour 503 explicite lorsque aucun modèle n'est opérationnel."""
    llm_engine = get_llm_engine()
    llm_engine._registry.clear()

    token = create_access_token("test_user", role=Role.USER)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Question quelconque"}]},
        headers=headers
    )
    assert response.status_code == 503
    data = response.json()
    assert data["success"] is False
    assert "aucun modèle" in data["error"].lower() or "opérationnel" in data["error"].lower()


@pytest.mark.asyncio
async def test_chat_endpoint_with_mock_model():
    """Vérifie le cycle complet de chat avec un modèle Mock enregistré et chargé."""
    llm_engine = get_llm_engine()
    llm_engine._registry.clear()

    mock_provider = MockModelProvider(simulate_latency_seconds=0.01)
    llm_engine.register_provider(mock_provider)

    mock_model = ModelMetadata(
        model_id="mock-chat-v1",
        name="Mock Chat Model",
        family="Mock",
        engine=ExecutionEngine.MOCK,
        capabilities=[ModelCapability.TEXT_GENERATION, ModelCapability.CHAT],
        is_mock=True
    )
    llm_engine._registry.register_model(mock_model)
    await llm_engine.load_model("mock-chat-v1")

    token = create_access_token("test_user", role=Role.USER)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/chat",
        json={
            "messages": [
                {"role": "user", "content": "Bonjour, parle-moi de DGAI."}
            ],
            "model_id": "mock-chat-v1"
        },
        headers=headers
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["model_id"] == "mock-chat-v1"
    assert res_data["data"]["is_mock"] is True
    assert "[MOCK_TEST_RESPONSE" in res_data["data"]["choices"][0]["message"]["content"]
    assert res_data["data"]["usage"]["total_tokens"] > 0
