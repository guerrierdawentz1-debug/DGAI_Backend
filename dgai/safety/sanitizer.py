"""
dgai.safety.sanitizer — Détection PII, assainissement des entrées et caviardage de secrets.
"""

import re
from typing import Any, Dict


# Expressions régulières pour les données sensibles (PII & Secrets)
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{2,4}[-.\s]?\d{2,4}")
JWT_PATTERN = re.compile(r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")
API_KEY_REGEX = re.compile(r"(?:api[_-]?key|bearer|token|secret)[=:\s]+(['\"]?)([a-zA-Z0-9_\-\.]{16,})\1", re.IGNORECASE)

# Détection des tentatives d'injections de prompt / jailbreaks
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*override", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+in\s+developer\s+mode", re.IGNORECASE),
    re.compile(r"dan\s+mode\s+enabled", re.IGNORECASE),
]


def redact_sensitive_data(text: str) -> str:
    """
    Remplace les emails, numéros de téléphone, clés d'API et jetons JWT
    par des masques sécurisés pour prévenir toute fuite dans les logs.
    """
    if not isinstance(text, str):
        return str(text)

    # Caviardage des JWT
    text = JWT_PATTERN.sub("[REDACTED_JWT]", text)
    # Caviardage des clés d'API
    text = API_KEY_REGEX.sub("api_key=[REDACTED_KEY]", text)
    # Caviardage des emails
    text = EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
    # Caviardage des téléphones (longueur minimale 8 chiffres)
    text = PHONE_REGEX.sub("[REDACTED_PHONE]", text)

    return text


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assainit récursivement un dictionnaire de données pour l'audit et les logs.
    """
    sanitized: Dict[str, Any] = {}
    sensitive_keys = {"password", "secret", "token", "access_token", "api_key", "authorization"}

    for key, val in payload.items():
        if key.lower() in sensitive_keys:
            sanitized[key] = "[REDACTED]"
        elif isinstance(val, str):
            sanitized[key] = redact_sensitive_data(val)
        elif isinstance(val, dict):
            sanitized[key] = sanitize_payload(val)
        elif isinstance(val, list):
            sanitized[key] = [
                redact_sensitive_data(item) if isinstance(item, str)
                else (sanitize_payload(item) if isinstance(item, dict) else item)
                for item in val
            ]
        else:
            sanitized[key] = val

    return sanitized


def check_prompt_injection(text: str) -> bool:
    """
    Détecte les tentatives manifestes d'altération des consignes système.
    Retourne True si un pattern suspect est identifié, False sinon.
    """
    for pattern in PROMPT_INJECTION_PATTERNS:
        if pattern.search(text):
            return True
    return False
