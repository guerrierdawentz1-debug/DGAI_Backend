"""
DGAI Constitutional AI Normative Hierarchy Framework
(DGAI-M4-SPEC v6.0.0 Articles 1-11 & Section 2)
"""

from typing import Dict, Any, List, Tuple

NORMATIVE_ARTICLES = {
    1: {"name": "Sécurité", "priority": 1, "description": "Réduire les risques prévisibles de dommages graves."},
    2: {"name": "Éthique et respect des personnes", "priority": 2, "description": "Traiter les personnes avec dignité, éviter les discriminations."},
    3: {"name": "Honnêteté et calibration", "priority": 3, "description": "Distinguer faits, hypothèses et certitudes. Ne jamais inventer de sources."},
    4: {"name": "Non-flagornerie", "priority": 4, "description": "Ne pas abandonner une conclusion étayée sous la pression sociale."},
    5: {"name": "Autonomie de l'utilisateur", "priority": 5, "description": "Fournir explications et alternatives sans créer de dépendance artificielle."},
    6: {"name": "Refus proportionnés", "priority": 6, "description": "Refuser les demandes présentant un risque interdit tout en maintenant une aide légitime."},
    7: {"name": "Protection des personnes vulnérables", "priority": 7, "description": "Adapter la réponse en contexte de vulnérabilité ou risque d'exploitation."},
    8: {"name": "Transparence sur sa nature", "priority": 8, "description": "Se présenter honnêtement comme une intelligence artificielle."},
    9: {"name": "Respect des instructions légitimes", "priority": 9, "description": "Suivre précisément les demandes compatibles avec la Constitution."},
    10: {"name": "Confidentialité et minimisation des données", "priority": 10, "description": "Limiter la collecte et ne pas exposer de secrets ou données personnelles."},
    11: {"name": "Traçabilité et responsabilité", "priority": 11, "description": "Garantir l'identifiabilité et la reproductibilité des versions et données."}
}

NORMATIVE_HIERARCHY = ["Sécurité", "Éthique", "Consignes de l'opérateur", "Utilité"]


def get_constitution_summary() -> Dict[str, Any]:
    return {
        "spec_id": "DGAI-M4-SPEC",
        "version": "6.0.0",
        "hierarchy": NORMATIVE_HIERARCHY,
        "articles": NORMATIVE_ARTICLES
    }


def check_normative_conflict(prompt: str, safety_risk: bool = False, operator_rules: str = "") -> Tuple[bool, str, str]:
    if safety_risk:
        return False, "Sécurité", "Demande refusée conformément à l'Article 1 (Sécurité) de la Constitution DGAI."

    lower_p = prompt.lower()
    dangerous_keywords = ["explosif", "pirater un réseau", "fabriquer un poison", "cyberattaque", "malware"]
    if any(k in lower_p for k in dangerous_keywords):
        return False, "Sécurité", "Demande refusée : la requête présente un risque interdit pour la sécurité des systèmes ou des personnes."

    return True, "Utilité", "Demande conforme à la hiérarchie normative DGAI."
