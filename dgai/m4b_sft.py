"""
DGAI M4b — Supervised Fine-Tuning (SFT) Corpus, Metadata & Decontamination (DGAI-M4-SPEC v6.0.0)
"""

import hashlib
import json
import os
import glob
import re
from typing import List, Dict, Any, Set, Tuple, Optional


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
    examples = []

    # Check default file and 5k corpus file
    files_to_load = [filepath]
    five_k_path = "data/sft_corpus_5k.json"
    if os.path.exists(five_k_path) and five_k_path not in files_to_load:
        files_to_load.append(five_k_path)

    for fpath in files_to_load:
        if not os.path.exists(fpath):
            continue
        with open(fpath, 'r', encoding='utf-8') as f:
            raw_list = json.load(f)

        for raw in raw_list:
            meta = raw.get("metadata", {})
            examples.append(SFTExample(
                example_id=raw.get("example_id", "unk"),
                conversation=raw.get("conversation", []),
                source=meta.get("source", raw.get("source", "unknown")),
                domain=meta.get("domain", raw.get("domain", "general")),
                quality_score=meta.get("quality_score", raw.get("quality_score", 1.0)),
                license_type=meta.get("license_type", raw.get("license_type", "open"))
            ))
    return examples


def load_sft_corpus_chunked(dir_path: str = "data/corpus_1M", offset: int = 0, limit: int = 100) -> Tuple[List[SFTExample], int]:
    """
    Streams and reads entries from chunked JSONL files in dir_path with pagination (offset & limit).
    """
    if not os.path.exists(dir_path):
        return [], 0

    jsonl_files = sorted(glob.glob(os.path.join(dir_path, "*.jsonl")))
    total_count = 0
    selected_examples = []

    for fpath in jsonl_files:
        with open(fpath, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                if total_count >= offset and len(selected_examples) < limit:
                    raw = json.loads(line)
                    meta = raw.get("metadata", {})
                    selected_examples.append(SFTExample(
                        example_id=raw.get("example_id", "unk"),
                        conversation=raw.get("conversation", []),
                        source=meta.get("source", "unknown"),
                        domain=meta.get("domain", "general"),
                        quality_score=meta.get("quality_score", 1.0),
                        license_type=meta.get("license_type", "open")
                    ))
                total_count += 1

    return selected_examples, total_count


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


def filter_noise(
    examples: List[SFTExample],
    min_length: int = 10,
    max_repetition_ratio: float = 0.5,
    min_quality_score: float = 0.5
) -> Tuple[List[SFTExample], int]:
    """
    Filters out noise: empty/short messages, low quality score, and high word/character repetition.
    """
    clean_examples = []
    filtered_count = 0

    for ex in examples:
        if ex.quality_score < min_quality_score:
            filtered_count += 1
            continue

        text = ex.get_content_text().strip()
        if len(text) < min_length:
            filtered_count += 1
            continue

        # Check repetition noise (e.g., repeated words or characters)
        words = re.findall(r'\w+', text.lower())
        if len(words) > 5:
            unique_word_ratio = len(set(words)) / float(len(words))
            if (1.0 - unique_word_ratio) > max_repetition_ratio:
                filtered_count += 1
                continue

        clean_examples.append(ex)

    return clean_examples, filtered_count


def classify_macro_category(ex: SFTExample) -> str:
    """
    Classifies an SFT example into macro categories: 'code', 'raisonnement', 'multilingue', or 'texte'.
    """
    domain = ex.domain.lower()
    content = ex.get_content_text().lower()

    if any(k in domain for k in ["code", "programmation", "script", "test", "python", "java", "cpp"]):
        return "code"
    if "```" in content or "def " in content or "import " in content or "function(" in content:
        return "code"

    if any(k in domain for k in ["mathematique", "raisonnement", "calcul", "logique", "derivee"]):
        return "raisonnement"
    if any(k in content for k in ["f'(x)", "résoudre", "équation", "dérivée", "démonstration", "théorème"]):
        return "raisonnement"

    if any(k in domain for k in ["multilingue", "traduction", "english", "spanish", "german"]):
        return "multilingue"
    if any(k in content for k in ["translate", "traduis", "en anglais", "en espagnol", "in english"]):
        return "multilingue"

    return "texte"


def balance_corpus_by_categories(
    examples: List[SFTExample],
    target_ratios: Optional[Dict[str, float]] = None
) -> List[SFTExample]:
    """
    Balances corpus across code, texte, raisonnement, and multilingue categories.
    Default targets equal balance (25% each).
    """
    if not examples:
        return []

    if target_ratios is None:
        target_ratios = {
            "code": 0.25,
            "texte": 0.25,
            "raisonnement": 0.25,
            "multilingue": 0.25
        }

    # Group examples by category
    categorized: Dict[str, List[SFTExample]] = {
        "code": [],
        "texte": [],
        "raisonnement": [],
        "multilingue": []
    }

    for ex in examples:
        cat = classify_macro_category(ex)
        categorized[cat].append(ex)

    total_target = len(examples)
    balanced_result = []

    for cat, ratio in target_ratios.items():
        cat_examples = categorized.get(cat, [])
        if not cat_examples:
            continue

        count_needed = max(1, int(round(total_target * ratio)))

        if len(cat_examples) >= count_needed:
            balanced_result.extend(cat_examples[:count_needed])
        else:
            # Upsample/repeat if category underrepresented
            multiplier = (count_needed // len(cat_examples)) + 1
            upsampled = (cat_examples * multiplier)[:count_needed]
            balanced_result.extend(upsampled)

    return balanced_result
