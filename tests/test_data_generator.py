"""
Unit and API Integration Tests for High-Capacity Synthetic Data Generator
(DGAI-M4-SPEC v6.0.0)
"""

import pytest
import json
from main import app
from dgai.m4b_data_generator import generate_sft_sample, generate_sft_batch, stream_sft_corpus, DOMAINS
from dgai.m4b_sft import deduplicate_examples


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
