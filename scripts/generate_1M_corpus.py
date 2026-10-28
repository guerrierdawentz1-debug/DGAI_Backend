#!/usr/bin/env python3
"""
DGAI-M4-SPEC v6.0.0 — 1 Million Dataset Generator Script
Generates 1,000,000 SFT examples saved in chunked JSONL format.
"""

import os
import sys
import json
import argparse

# Ensure current working directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dgai.m4b_data_generator import generate_sft_sample, DOMAINS


def generate_1M_corpus(target_dir: str = "data/corpus_1M", total_samples: int = 1000000, chunk_size: int = 10000):
    os.makedirs(target_dir, exist_ok=True)
    num_chunks = (total_samples + chunk_size - 1) // chunk_size

    print(f"Starting generation of {total_samples:,} SFT samples in {num_chunks} chunk files...")

    generated = 0
    for chunk_idx in range(num_chunks):
        chunk_file = os.path.join(target_dir, f"sft_part_{chunk_idx+1:03d}.jsonl")
        count_this_chunk = min(chunk_size, total_samples - generated)

        with open(chunk_file, "w", encoding="utf-8") as f:
            for i in range(count_this_chunk):
                sample_idx = generated + i
                domain = DOMAINS[sample_idx % len(DOMAINS)]
                sample = generate_sft_sample(sample_idx, domain=domain)
                f.write(json.dumps(sample.to_dict(), ensure_ascii=False) + "\n")

        generated += count_this_chunk
        print(f"Generated chunk {chunk_idx+1}/{num_chunks}: {chunk_file} ({generated:,}/{total_samples:,})")

    print(f"Successfully generated {generated:,} dataset entries in '{target_dir}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 1 Million SFT samples for DGAI-M4-SPEC")
    parser.add_argument("--dir", type=str, default="data/corpus_1M", help="Target directory for dataset chunks")
    parser.add_argument("--count", type=int, default=1000000, help="Number of samples to generate (default: 1,000,000)")
    parser.add_argument("--chunk_size", type=int, default=5000, help="Chunk size per JSONL file")
    args = parser.parse_args()

    generate_1M_corpus(target_dir=args.dir, total_samples=args.count, chunk_size=args.chunk_size)
