"""
Unit and API Integration Tests for Response Style Formatting
(DGAI-M4-SPEC v6.0.0 Section 3 & 4)
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


def test_short_style():
    raw = "La vitesse de la lumière est de 300 000 km/s. C'est une constante physique universelle."
    res = format_response_by_style("quelle vitesse?", raw, style="short")
    assert res["style"] == "short"
    assert "300 000 km/s" in res["formatted_response"]


def test_detailed_style():
    raw = "Explication détaillée de la théorie."
    res = format_response_by_style("explique", raw, style="detailed")
    assert res["style"] == "detailed"
    assert "Explication détaillée" in res["formatted_response"]


def test_bullet_points_style():
    raw = "Premier point important. Deuxième point fondamental."
    res = format_response_by_style("liste", raw, style="bullet_points")
    assert res["style"] == "bullet_points"
    assert "•" in res["formatted_response"]


def test_structured_style():
    raw = "Contenu structuré avec titre."
    res = format_response_by_style("structure", raw, style="structured")
    assert res["style"] == "structured"
    assert "### Réponse DGAI" in res["formatted_response"]


def test_style_format_api_endpoint(client):
    rv = client.post('/api/v1/m4a/style_format', json={
        "prompt": "Explique la gravité",
        "content": "La gravité attire les masses.",
        "style": "bullet_points"
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert "•" in data["result"]["formatted_response"]
