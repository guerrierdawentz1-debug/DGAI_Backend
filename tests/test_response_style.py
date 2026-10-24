"""
Unit and Integration Tests for Flexible Response Style Controller
(DGAI-M4-SPEC v6.0.0 M4a & M4e)
"""

import pytest
import json
from main import app
from dgai.response_style import format_response_by_style


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_short_and_concise_style():
    prompt = "Quelle est la capitale de la France ?"
    content = "La capitale de la France est Paris. C'est une grande métropole européenne avec une riche histoire."
    res = format_response_by_style(prompt, content, style="short", max_words=10)
    assert res["style"] == "short"
    assert "Paris" in res["formatted_response"]
    assert res["word_count"] <= 12


def test_detailed_style():
    prompt = "Explique le fonctionnement du moteur à explosion."
    content = "Le moteur à explosion transforme l'énergie thermique du carburant en énergie mécanique."
    res = format_response_by_style(prompt, content, style="detailed")
    assert res["style"] == "detailed"
    assert "Contexte & Analyse" in res["formatted_response"]
    assert "En résumé" in res["formatted_response"]


def test_bullet_points_style():
    prompt = "Liste trois fruits rouges."
    content = "Fraise est un fruit rouge. Framboise est délicieuse. Cerise est sucrée."
    res = format_response_by_style(prompt, content, style="bullet_points")
    assert res["style"] == "bullet_points"
    assert "•" in res["formatted_response"]


def test_structured_style():
    prompt = "Analyse l'impact de l'IA."
    content = "L'intelligence artificielle automatise les tâches et accélère l'innovation."
    res = format_response_by_style(prompt, content, style="structured")
    assert res["style"] == "structured"
    assert "### Aperçu" in res["formatted_response"]
    assert "### Analyse Détaillée" in res["formatted_response"]


def test_style_format_api_endpoint(client):
    rv = client.post('/api/v1/m4a/style_format', json={
        "prompt": "Explique la gravité.",
        "content": "La gravité est une force d'attraction fondamentale.",
        "style": "bullet_points"
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert "•" in data["result"]["formatted_response"]
