"""
Unit and API Integration Tests for High-Capacity Synthetic Data Generator
(DGAI-M4-SPEC v6.0.0)
"""

import pytest
import json
from main import app
from dgai.m4b_data_generator import generate_sft_sample, generate_sft_batch, stream_sft_corpus, DOMAINS, calculate_chinchilla_token_ratio, estimate_dataset_token_count
from dgai.m4b_sft import deduplicate_examples, load_sft_corpus_chunked


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_generator_domains_and_sample():
    assert len(DOMAINS) == 16
    sample = generate_sft_sample(42)
    sample_dict = sample.to_dict()
    assert sample_dict["example_id"] == "synth_sft_0000042"
    assert len(sample.conversation) >= 2


def test_batch_and_stream_generator():
    batch = generate_sft_batch(start_index=0, count=50)
    assert len(batch) == 50

    # Stream generator
    gen = stream_sft_corpus(total_count=2500, batch_size=1000)
    batches = list(gen)
    assert len(batches) == 3
    assert len(batches[0]) == 1000
    assert len(batches[1]) == 1000
    assert len(batches[2]) == 500


def test_deduplication_on_synthetic_samples():
    samples = generate_sft_batch(start_index=0, count=100)
    deduped = deduplicate_examples(samples)
    assert len(deduped) <= len(samples)
    assert len(deduped) > 0


def test_generate_corpus_api_endpoint(client):
    rv = client.post('/api/v1/m4b/sft/generate_corpus', json={
        "start_index": 1000,
        "count": 50,
        "domain": "questions_factuelles"
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert data["count"] == 50
    assert data["total_available_capacity"] == 1000000
    assert len(data["samples"]) == 50
    assert data["samples"][0]["metadata"]["domain"] == "questions_factuelles"


def test_chunked_corpus_loader_and_api(client):
    # Load via python function
    samples, total = load_sft_corpus_chunked(dir_path="data/corpus_1M", offset=0, limit=25)
    assert total >= 10000
    assert len(samples) == 25

    # Load via API
    rv = client.post('/api/v1/m4b/sft/corpus_chunked', json={
        "dir_path": "data/corpus_1M",
        "offset": 50,
        "limit": 30
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert data["returned_count"] == 30
    assert data["total_corpus_count"] >= 10000


def test_chinchilla_scaling_metrics_and_api(client):
    samples = generate_sft_batch(start_index=0, count=50)
    est = estimate_dataset_token_count(samples)
    assert est["example_count"] == 50
    assert est["estimated_tokens"] > 0

    chinchilla = calculate_chinchilla_token_ratio(num_parameters=1000000, num_tokens=100000000)
    assert chinchilla["is_chinchilla_optimal"] is True
    assert chinchilla["is_overtrained_optimal"] is True
    assert chinchilla["status"] == "overtrained_optimal"

    # API test
    rv = client.post('/api/v1/m4b/sft/token_scaling_metrics', json={
        "num_parameters": 10000000,
        "num_tokens": 500000000
    })
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"
    assert data["scaling_metrics"]["is_chinchilla_optimal"] is True
