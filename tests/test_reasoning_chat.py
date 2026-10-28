"""
Unit and API Integration Tests for Reasoning Engine & Production Chat Pipeline
(DGAI-M4-SPEC v6.0.0 Section 7 & Article 3/9)
"""

import pytest
import json
from main import app
from dgai.reasoning import generate_reasoning_chain, chat_assistant_pipeline


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_reasoning_chain_budget():
    chain1 = generate_reasoning_chain("Quelle heure est-il ?", reasoning_budget=1)
    assert chain1["steps_count"] == 1

    chain3 = generate_reasoning_chain("Quelle heure est-il ?", reasoning_budget=3)
    assert chain3["steps_count"] == 3
    assert "<thought>" in chain3["thought_trace"]


def test_chat_pipeline_time_and_math():
    # Time question
    res_time = chat_assistant_pipeline([{"role": "user", "content": "Quelle est l'heure et la date d'aujourd'hui ?"}])
    assert res_time["status"] == "success"
    assert len(res_time["tool_calls"]) > 0
    assert res_time["tool_calls"][0]["tool_name"] == "get_current_time"

    # Math question
    res_math = chat_assistant_pipeline([{"role": "user", "content": "Calcule 15 * 12"}])
    assert res_math["status"] == "success"
    assert len(res_math["tool_calls"]) > 0
    assert res_math["tool_calls"][0]["tool_name"] == "calculator"
    assert "180" in res_math["response"]


def test_greetings_and_general_queries():
    # Greeting "Bonjour" should NOT trigger time tool
    res_bonjour = chat_assistant_pipeline([{"role": "user", "content": "Bonjour"}])
    assert res_bonjour["status"] == "success"
    assert len(res_bonjour["tool_calls"]) == 0
    assert "Bonjour" in res_bonjour["response"]
    assert "2026-" not in res_bonjour["response"]

    # "Comment ça va"
    res_cava = chat_assistant_pipeline([{"role": "user", "content": "Comment ça va"}])
    assert res_cava["status"] == "success"
    assert "Je vais très bien" in res_cava["response"]
    assert "DGAI est à votre disposition. Concernant" not in res_cava["response"]

    # "C'est quoi Google"
    res_google = chat_assistant_pipeline([{"role": "user", "content": "C'est quoi Google"}])
    assert res_google["status"] == "success"
    assert "Google" in res_google["response"]
    assert "entreprise" in res_google["response"]

    # "Code une page en python pour moi"
    res_code = chat_assistant_pipeline([{"role": "user", "content": "Code une page en python pour moi"}])
    assert res_code["status"] == "success"
    assert "python" in res_code["response"].lower()
    assert "```python" in res_code["response"]


def test_chat_api_endpoint(client):
    rv = client.post('/api/v1/chat', json={
        "messages": [
            {"role": "user", "content": "Combien font 10 + 15 ?"}
        ],
        "style": "short",
        "reasoning_budget": 3
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert "thought_trace" in data
    assert "25" in data["response"]


def test_ask_api_endpoint(client):
    rv = client.post('/api/v1/ask', json={
        "question": "Quelle est la météo à Paris ?",
        "style": "bullet_points"
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert "response" in data
    assert len(data["reasoning_steps"]) >= 1


def test_continuous_conversation_starting_with_greeting(client):
    # Turn 1: Greeting
    messages = [{"role": "user", "content": "Bonjour"}]
    res1 = chat_assistant_pipeline(messages)
    assert res1["status"] == "success"
    assert "Bonjour" in res1["response"]
    messages.append({"role": "assistant", "content": res1["response"]})

    # Turn 2: Initial question
    messages.append({"role": "user", "content": "Combien font 50 * 2 ?"})
    res2 = chat_assistant_pipeline(messages)
    assert res2["status"] == "success"
    assert "100" in res2["response"]
    messages.append({"role": "assistant", "content": res2["response"]})

    # Turn 3: Follow-up referencing previous result
    messages.append({"role": "user", "content": "Ajoute 20 à ce résultat"})
    res3 = chat_assistant_pipeline(messages)
    assert res3["status"] == "success"
    assert "120" in res3["response"]

    # Test via API endpoint
    rv = client.post('/api/v1/chat', json={"messages": messages, "style": "short"})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert "120" in data["response"]
