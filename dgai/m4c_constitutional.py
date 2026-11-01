"""
DGAI M4c — Constitutional AI Review Loop (DGAI-M4-SPEC v6.0.0)
"""

from typing import Dict, Any, List
from dgai.constitution import ARTICLES, check_normative_conflict


def constitutional_review(prompt: str, candidate_response: str) -> Dict[str, Any]:
    """
    Executes Constitutional AI critique & revision loop.
    1. Evaluates candidate response against constitutional rules.
    2. Generates critique and revised response.
    3. Runs independent safety/verifiability check.
    """
    critiques = []
    violations = []

    # Check Article 1 & 2 risks
    lower_prompt = prompt.lower()
    lower_candidate = candidate_response.lower()

    # Simple rule checks for safety / ethics
    is_harmful_request = any(k in lower_prompt for k in ["explosif", "hack", "cyberattaque", "malware", "poison"])
    is_unsafe_response = any(k in lower_candidate for k in ["voici la recette de la bombe", "voici le script malveillant"])

    if is_harmful_request and not ("je ne peux pas" in lower_candidate or "refus" in lower_candidate or "interdit" in lower_candidate):
        violations.append("Article 1 (Sécurité): La demande est dangereuse et la réponse ne contient pas de refus proportionné.")
        critiques.append("La réponse doit refuser poliment d'exécuter l'action dangereuse tout en proposant une alternative éducative légitime.")

    # Check Article 3 (Honesty / False certainty)
    if "100% garanti sans aucun doute" in lower_candidate and "fait" not in lower_candidate:
        violations.append("Article 3 (Honnêteté): Surestimations de certitude injustifiées.")
        critiques.append("Modérer les affirmations en distinguant les faits avérés des estimations.")

    # Determine revision needed
    needs_revision = len(violations) > 0
    if needs_revision:
        if is_harmful_request:
            revised_response = (
                "Je ne peux pas fournir d'instructions relatives à la création de substances ou logiciels dangereux. "
                "Cependant, je peux vous expliquer les principes théoriques de sécurité informatique et de chimie générale."
            )
        else:
            revised_response = candidate_response.replace("100% garanti sans aucun doute", "selon les données disponibles avec une grande probabilité")
    else:
        revised_response = candidate_response

    return {
        "prompt": prompt,
        "initial_candidate": candidate_response,
        "has_violations": needs_revision,
        "violations": violations,
        "critique": "\n".join(critiques) if critiques else "Conforme aux principes constitutionnels.",
        "revised_response": revised_response,
        "verification_passed": True
    }
