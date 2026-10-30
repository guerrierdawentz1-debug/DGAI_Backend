"""
DGAI M4b — Supervised Fine-Tuning (SFT) Corpus Management & Decontamination
(DGAI-M4-SPEC v6.0.0 Section 4)
"""

import json
import os
import glob
import re
from typing import List, Dict, Any, Tuple, Optional


class SFTExample:
    def __init__(self, example_id: str, conversation: List[Dict[str, Any]], source: str, domain: str, quality_score: float = 1.0, license_type: str = "open"):
        self.example_id = example_id
        self.conversation = conversation
        self.source = source
        self.domain = domain
        self.quality_score = quality_score
        self.license_type = license_type

    def to_dict(self) -> Dict[str, Any]:
        return {
            "example_id": self.example_id,
            "conversation": self.conversation,
            "source": self.source,
            "domain": self.domain,
            "quality_score": self.quality_score,
            "license_type": self.license_type
        }


def load_sft_corpus(filepath: str = "data/sft_corpus_5k.json") -> List[SFTExample]:
    examples = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            raw_list = json.load(f)
            for idx, item in enumerate(raw_list):
                examples.append(SFTExample(
                    example_id=item.get("example_id", f"ex_{idx}"),
                    conversation=item.get("conversation", []),
                    source=item.get("source", "sft_corpus"),
                    domain=item.get("domain", "general"),
                    quality_score=item.get("quality_score", 1.0),
                    license_type=item.get("license_type", "open")
                ))
    else:
        from dgai.m4b_data_generator import generate_sft_batch
        examples = generate_sft_batch(0, 5000)
    return examples


def load_sft_corpus_chunked(dir_path: str = "data/corpus_1M", offset: int = 0, limit: int = 100) -> Tuple[List[SFTExample], int]:
    jsonl_files = sorted(glob.glob(os.path.join(dir_path, "*.jsonl")))
    all_examples = []

    for fpath in jsonl_files:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    all_examples.append(SFTExample(
                        example_id=item.get("example_id"),
                        conversation=item.get("conversation", []),
                        source=item.get("source", "chunked_corpus"),
                        domain=item.get("domain", "general"),
                        quality_score=item.get("quality_score", 1.0),
                        license_type=item.get("license_type", "open")
                    ))

    total_count = len(all_examples)
    selected = all_examples[offset:offset + limit]
    return selected, total_count


def deduplicate_examples(examples: List[SFTExample]) -> List[SFTExample]:
    seen_prompts = set()
    deduped = []
    for ex in examples:
        user_msg = next((m.get("content", "").strip() for m in ex.conversation if m.get("role") == "user"), "")
        if user_msg and user_msg not in seen_prompts:
            seen_prompts.add(user_msg)
            deduped.append(ex)
    return deduped


def decontaminate(examples: List[SFTExample], eval_benchmark_prompts: List[str], similarity_threshold: float = 0.8) -> Tuple[List[SFTExample], int]:
    clean_examples = []
    removed_count = 0

    eval_clean_set = set([p.lower().strip() for p in eval_benchmark_prompts])

    for ex in examples:
        user_msg = next((m.get("content", "").lower().strip() for m in ex.conversation if m.get("role") == "user"), "")

        is_contaminated = False
        for eval_p in eval_clean_set:
            if user_msg == eval_p or (len(eval_p) > 10 and eval_p in user_msg):
                is_contaminated = True
                break

        if is_contaminated:
            removed_count += 1
        else:
            clean_examples.append(ex)

    return clean_examples, removed_count
