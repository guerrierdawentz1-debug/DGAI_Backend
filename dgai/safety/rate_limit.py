"""
dgai.safety.rate_limit — Système de limitation de débit (Rate Limiting).

Implémentation par fenêtre glissante (Sliding Window Log) thread-safe.
Pour les déploiements multi-instances / clusters à grande échelle,
une implémentation adossée à Redis sera branchée via la même interface.
"""

import threading
import time
from collections import defaultdict
from typing import Dict, List
from dgai.core.config import get_settings


class InMemoryRateLimiter:
    """
    Limiteur de débit en mémoire basé sur un journal d'horodatages par clé (IP ou identifiant).
    Thread-safe pour les requêtes concurrentes.
    """

    def __init__(self, requests_per_minute: int | None = None):
        self._custom_limit = requests_per_minute
        self._lock = threading.Lock()
        self._records: Dict[str, List[float]] = defaultdict(list)

    @property
    def limit(self) -> int:
        if self._custom_limit is not None:
            return self._custom_limit
        return get_settings().rate_limit_requests_per_minute

    def is_allowed(self, identifier: str) -> bool:
        """
        Détermine si une requête provenant de l'identifiant (ex: IP) est autorisée.
        Retourne True si dans la limite, False en cas de dépassement.
        """
        now = time.time()
        window_start = now - 60.0  # Fenêtre de 60 secondes

        with self._lock:
            timestamps = self._records[identifier]

            # Élaguer les requêtes antérieures à la fenêtre
            valid_timestamps = [t for t in timestamps if t > window_start]
            self._records[identifier] = valid_timestamps

            if len(valid_timestamps) >= self.limit:
                return False

            self._records[identifier].append(now)
            return True

    def reset(self) -> None:
        """Réinitialise tous les compteurs (utile pour les tests)."""
        with self._lock:
            self._records.clear()


# Instance globale partagée
_rate_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    return _rate_limiter
