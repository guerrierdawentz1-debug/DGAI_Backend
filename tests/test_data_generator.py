"""
Unit Tests for Scalable SFT Synthetic Data Generator (Capacity: 1,000,000)
(DGAI-M4-SPEC v6.0.0 Section 4)
"""

import pytest
from dgai.m4b_data_generator import generate_sft_sample, generate_sft_batch, stream_sft_corpus, DOMAINS


def test_generate_sft_sample_domains():
    sample0 = generate_sft_sample(0)
    assert sample0.example_id == "synth_sft_0000000"
    assert sample0.domain in DOMAINS
    assert len(sample0.conversation) >= 2


def test_generate_sft_batch():
    batch = generate_sft_batch(start_index=100, count=50)
    assert len(batch) == 50
    assert batch[0].example_id == "synth_sft_0000100"


def test_stream_sft_corpus():
    gen = stream_sft_corpus(total_count=2500, batch_size=1000)
    batches = list(gen)
    assert len(batches) == 3
    assert len(batches[0]) == 1000
    assert len(batches[1]) == 1000
    assert len(batches[2]) == 500
