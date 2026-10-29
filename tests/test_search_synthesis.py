"""
Unit and API Integration Tests for Search-Grounded Retrieval and Synthesis
(DGAI-M4-SPEC v6.0.0 Article 3 & 0.1)
"""

import pytest
import json
from main import app
from dgai.m4b_sft import load_sft_corpus
from dgai.search_engine import search_and_synthesize


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_5k_sft_corpus_loading():
    corpus = load_sft_corpus()
    assert len(corpus) >= 5000


def test_search_and_synthesize_engine():
    res = search_and_synthesize("astronomie astrophysique")
    assert res["grounded"] is True
    assert "tool_call" in res
    assert len(res["sources"]) > 0
    assert "D'après les résultats" in res["synthesized_response"]


def test_search_and_synthesize_api_endpoint(client):
    rv = client.post('/api/v1/m4f/search_and_synthesize', json={
        "query": "technologie DGAI 2026",
        "search_results": [
            {
                "title": "Specs DGAI",
                "snippet": "DGAI M4 spécification version 6.0.0 publiée avec succès.",
                "source_url": "https://dgai.internal/spec/6.0.0"
            }
        ]
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    result = data["result"]
    assert result["grounded"] is True
    assert "DGAI M4 spécification version 6.0.0" in result["synthesized_response"]
    assert "https://dgai.internal/spec/6.0.0" in result["sources"]
