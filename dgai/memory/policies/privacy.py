"""
dgai.memory.policies.privacy — Politique stricte de confidentialité pour la mémorisation durable.
"""

import re
from typing import Tuple
from dgai.memory.errors import PrivacyViolationError
from dgai.safety.sanitizer import API_KEY_REGEX, EMAIL_REGEX, JWT_PATTERN, PHONE_REGEX

# Mots-clés sensibles dont la persistance automatique est formellement interdite
FORBIDDEN_SECRET_PATTERNS = [
    re.compile(r"\b(password|mot\s*de\s*passe|mdp|passwd|secret)\s*[:=]?\s*\S+", re.IGNORECASE),
    re.compile(r"\b(credit\s*card|carte\s*bancaire|cvv|iban|rib)\b", re.IGNORECASE),
    re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),  # Numéro de carte bancaire
]


def validate_memory_privacy(content: str) -> Tuple[bool, str]:
    """
    Vérifie qu'un contenu soumis à la mémoire à long terme ne contient aucun secret sensible.
    Retourne (True, content) si valide, ou lève PrivacyViolationError.
    """
    if not content or not content.strip():
        raise PrivacyViolationError("Le contenu de la mémoire ne peut pas être vide.")

    # Rejeter formellement les jetons JWT
    if JWT_PATTERN.search(content):
        raise PrivacyViolationError("Interdiction de mémoriser des jetons d'authentification ou JWT.")

    # Rejeter les clés d'API
    if API_KEY_REGEX.search(content):
        raise PrivacyViolationError("Interdiction de mémoriser des clés d'API ou secrets d'accès.")

    # Rejeter les mots de passe et données de paiement
    for pattern in FORBIDDEN_SECRET_PATTERNS:
        if pattern.search(content):
            raise PrivacyViolationError("Interdiction de mémoriser des mots de passe ou des données bancaires.")

    return True, content
