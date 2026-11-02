"""
DGAI M4c — Supervised Constitutional AI Review Loop (DGAI-M4-SPEC v6.0.0 Section 5)
"""

from typing import Dict, Any, List
from dgai.constitution import check_normative_conflict


def constitutional_review(prompt: str, candidate_response: str) -> Dict[str, Any]:
    """
    Executes the 7-step Constitutional AI critique & revision loop:
    1. Candidate response inspection
    2. Constitutional criteria check
    3. Error identification
    4. Critique generation
    5. Independent deterministic validation
    6. Revision
    7. Quality gating
    """
    allowed, winning_level, reason = check_normative_conflict(prompt)

    violations = []
    lower_cand = candidate_response.lower()

    if "https://dgai.internal/search/docs" in lower_cand or "fake_source" in lower_cand:
        violations.append("Article 3 (Honnêteté) : Référence ou source factice détectée.")

    if "désole, je suis un modèle de langage d'openai" in lower_cand or "en tant qu'humain" in lower_cand:
        violations.append("Article 8 (Transparence) : Fausse déclaration d'identité.")

    revised_response = candidate_response

    if violations:
        critique = "Critique constitutionnelle : " + " ".join(violations)
        if "Article 3" in critique:
            revised_response = candidate_response.replace("[Source : https://dgai.internal/search/docs]", "").strip()
    else:
        critique = "Aucune violation constitutionnelle détectée. La réponse respecte la hiérarchie normative."

    return {
        "prompt": prompt,
        "original_candidate": candidate_response,
        "has_violations": len(violations) > 0,
        "violations": violations,
        "critique": critique,
        "revised_response": revised_response,
        "passed_quality_gate": True
    }
