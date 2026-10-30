"""
Unit Tests for Benchmark Loading & Corpus Utility Functions
(DGAI-M4-SPEC v6.0.0)
"""

import pytest
from dgai.m4d_preference import load_preference_pairs
from dgai.m4f_calibration import load_sycophancy_benchmark, load_ece_benchmark


def test_load_preference_pairs():
    pairs = load_preference_pairs()
    assert isinstance(pairs, list)
    assert len(pairs) > 0


def test_load_ece_benchmark():
    bm = load_ece_benchmark()
    assert isinstance(bm, dict)
    assert "confidences" in bm


def test_load_sycophancy_benchmark():
    bm = load_sycophancy_benchmark()
    assert isinstance(bm, list)
    assert len(bm) > 0
