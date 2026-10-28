"""
DGAI M4b — Supervised Fine-Tuning (SFT) Corpus, Metadata & Decontamination (DGAI-M4-SPEC v6.0.0)
"""

import hashlib
import json
import os
import re
from typing import List, Dict, Any, Set, Tuple


class SFTExample:
    def __init__(self, example_id: str, conversation: List[Dict[str, Any]], source: str, domain: str, quality_score: float = 1.0, license_type: str = "open"):
        self.example_id = example_id
        self.conversation = conversation
        self.source = source
        self.domain = domain
        self.quality_score = quality_score
        self.license_type = license_type

    def get_content_text(self) -> str:
        text_parts = []
        for msg in self.conversation:
            text_parts.append(f"{msg.get('content', '')}")
        return "\n".join(text_parts)

    def compute_hash(self) -> str:
        return hashlib.sha256(self.get_content_text().encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "example_id": self.example_id,
            "conversation": self.conversation,
            "metadata": {
                "source": self.source,
                "domain": self.domain,
                "quality_score": self.quality_score,
                "license_type": self.license_type,
                "hash": self.compute_hash()
            }
        }


def load_sft_corpus(filepath: str = "data/sft_corpus.json") -> List[SFTExample]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_list = json.load(f)

    examples = []
    for raw in raw_list:
        examples.append(SFTExample(
            example_id=raw.get("example_id", "unk"),
            conversation=raw.get("conversation", []),
            source=raw.get("source", "unknown"),
            domain=raw.get("domain", "general"),
            quality_score=raw.get("quality_score", 1.0),
            license_type=raw.get("license_type", "open")
        ))
    return examples


def deduplicate_examples(examples: List[SFTExample]) -> List[SFTExample]:
    seen_hashes: Set[str] = set()
    deduped = []
    for ex in examples:
        h = ex.compute_hash()
        if h not in seen_hashes:
            seen_hashes.add(h)
            deduped.append(ex)
    return deduped


def decontaminate(train_examples: List[SFTExample], eval_benchmark_prompts: List[str], similarity_threshold: float = 0.8) -> Tuple[List[SFTExample], int]:
    """
    Filters out training examples that overlap significantly with evaluation benchmark prompts.
    """
    clean_examples = []
    removed_count = 0

    # Tokenize eval prompts
    eval_token_sets = [set(re.findall(r'\w+', p.lower())) for p in eval_benchmark_prompts if p.strip()]

    for ex in train_examples:
        content = ex.get_content_text().lower()
        ex_tokens = set(re.findall(r'\w+', content))
        is_contaminated = False

        if ex_tokens:
            for eval_tokens in eval_token_sets:
                if not eval_tokens:
                    continue
                intersection = ex_tokens.intersection(eval_tokens)
                jaccard = len(intersection) / float(len(eval_tokens))  # ratio of benchmark tokens found in example
                if jaccard >= similarity_threshold:
                    is_contaminated = True
                    break

        if is_contaminated:
            removed_count += 1
        else:
            clean_examples.append(ex)

    return clean_examples, removed_count
