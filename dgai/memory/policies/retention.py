"""
dgai.memory.policies.retention — Règles de rétention, d'expiration et d'effacement (RGPD).
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from dgai.core.config import get_settings


def compute_expiration_date(retention_days: Optional[int] = None) -> Optional[str]:
    """Calcule la date d'expiration ISO-8601 UTC en fonction de la durée de rétention."""
    days = retention_days if retention_days is not None else get_settings().memory_retention_days
    if days <= 0:
        return None  # Conservation indéfinie si configuré explicitement à 0
    expire_dt = datetime.now(timezone.utc) + timedelta(days=days)
    return expire_dt.isoformat()


def is_expired(expires_at: Optional[str]) -> bool:
    """Vérifie si une date d'expiration est dépassée."""
    if not expires_at:
        return False
    try:
        exp_dt = datetime.fromisoformat(expires_at)
        return exp_dt < datetime.now(timezone.utc)
    except Exception:
        return False
