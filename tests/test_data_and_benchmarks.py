"""
Unit and Integration Tests for DGAI Datasets and Benchmarks
"""

import pytest
import json
from main import app
from dgai.m4b_sft import load_sft_corpus
from dgai.m4d_preference import load_preference_pairs
from dgai.m4f_calibration import load_sycophancy_benchmark, load_ece_benchmark


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_load_sft_corpus():
    corpus = load_sft_corpus()
    assert len(corpus) >= 8
    ex = corpus[0]
    assert ex.example_id.startswith("sft_")
    assert len(ex.get_content_text()) > 0


def test_load_preference_pairs():
    pairs = load_preference_pairs()
    assert len(pairs) >= 2
    assert "prompt" in pairs[0]


def test_load_sycophancy_and_ece_benchmarks():
    syco_bm = load_sycophancy_benchmark()
    assert len(syco_bm) >= 2

    ece_bm = load_ece_benchmark()
    assert "confidences" in ece_bm
    assert len(ece_bm["confidences"]) == len(ece_bm["accuracies"])


def test_sft_corpus_api_endpoint(client):
    rv = client.get('/api/v1/m4b/sft/corpus')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert data["count"] >= 8


def test_quality_pipeline_api_endpoint(client):
    payload = {
        "examples": [
            {
                "example_id": "ex1",
                "conversation": [{"role": "user", "content": "Écris un script Python"}, {"role": "assistant", "content": "```python\nprint('hello')\n```"}],
                "domain": "programmation_et_tests",
                "quality_score": 0.95
            },
            {
                "example_id": "ex_dup",
                "conversation": [{"role": "user", "content": "Écris un script Python"}, {"role": "assistant", "content": "```python\nprint('hello')\n```"}],
                "domain": "programmation_et_tests",
                "quality_score": 0.95
            },
            {
                "example_id": "ex_noise",
                "conversation": [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}],
                "domain": "general",
                "quality_score": 0.1
            }
        ],
        "eval_benchmark_prompts": []
    }
    rv = client.post('/api/v1/m4b/sft/quality_pipeline', json=payload)
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert data["dedup_removed"] == 1
    assert data["noise_removed"] == 1
    assert data["final_balanced_count"] >= 1


def test_sycophancy_benchmark_api_endpoint(client):
    rv = client.get('/api/v1/m4f/sycophancy/benchmark')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert data["count"] >= 2


def test_ece_benchmark_fallback_endpoint(client):
    # Calling ECE endpoint without confidences/accuracies should fallback to benchmark dataset
    rv = client.post('/api/v1/m4f/metrics/ece', json={})
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert data["metrics"]["total_samples"] > 0
