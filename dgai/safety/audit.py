"""
dgai.safety.audit — Journalisation d'audit des événements de sécurité.

Trace les tentatives d'authentification, refus d'accès, erreurs de validation
et actions sensibles sans JAMAIS consigner de secrets ou de contenus privés en clair.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from dgai.core.logging import get_logger
from dgai.safety.sanitizer import sanitize_payload

audit_logger = get_logger("audit")


class SecurityEventType(str, Enum):
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    ACCESS_DENIED = "access_denied"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    VALIDATION_ERROR = "validation_error"
    PAYLOAD_TOO_LARGE = "payload_too_large"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    CONFIG_CHANGED = "config_changed"


def log_security_event(
    event_type: SecurityEventType,
    client_ip: str,
    endpoint: str,
    actor: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    level: str = "WARNING"
) -> None:
    """
    Écrit un événement d'audit sécurisé et assaini dans les journaux structurés.
    """
    safe_details = sanitize_payload(details) if details else {}

    audit_entry = {
        "event_type": event_type.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "client_ip": client_ip,
        "endpoint": endpoint,
        "actor": actor or "anonymous",
        "details": safe_details
    }

    log_method = getattr(audit_logger, level.lower(), audit_logger.warning)
    log_method(f"Security Event: {event_type.value} on {endpoint} by {actor or 'anonymous'}", extra={"context": audit_entry})
