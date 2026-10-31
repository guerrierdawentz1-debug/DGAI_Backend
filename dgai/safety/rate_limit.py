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


from abc import ABC, abstractmethod


class BaseRateLimiter(ABC):
    """Interface abstraite pour les limiteurs de débit (In-Memory, Redis, Cluster)."""

    @abstractmethod
    def is_allowed(self, identifier: str) -> bool:
        """Indique si la requête est autorisée pour l'identifiant donné."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Réinitialise les états de limitation."""
        pass


class InMemoryRateLimiter(BaseRateLimiter):
    """
    Limiteur de débit en mémoire basé sur un journal d'horodatages par clé (IP ou identifiant).
    Thread-safe pour les requêtes concurrentes, avec protection contre l'épuisement mémoire (max 10 000 clés).

    LIMITATION ARCHITECTURALE :
    Ce limiteur opère exclusivement dans la mémoire du processus courant.
    Dans un environnement multi-processus (ex: Gunicorn avec 4 workers) ou multi-conteneurs,
    les quotas sont gérés par worker. Pour un cluster distribué, l'interface `BaseRateLimiter`
    devra être implémentée avec un backend Redis / Valkey.
    """

    MAX_TRACKED_IDENTIFIERS = 10000

    def __init__(self, requests_per_minute: int | None = None):
        self._custom_limit = requests_per_minute
        self._lock = threading.Lock()
        self._records: Dict[str, List[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    @property
    def limit(self) -> int:
        if self._custom_limit is not None:
            return self._custom_limit
        return get_settings().rate_limit_requests_per_minute

    def _cleanup_expired(self, now: float, force: bool = False) -> None:
        """Purge périodique des clés inactives pour prévenir les fuites de mémoire."""
        if not force and (now - self._last_cleanup < 30.0 and len(self._records) < self.MAX_TRACKED_IDENTIFIERS):
            return

        window_start = now - 60.0
        keys_to_delete = []
        for ident, ts_list in list(self._records.items()):
            valid = [t for t in ts_list if t > window_start]
            if not valid:
                keys_to_delete.append(ident)
            else:
                self._records[ident] = valid

        for k in keys_to_delete:
            if k in self._records:
                del self._records[k]

        self._last_cleanup = now

    def is_allowed(self, identifier: str) -> bool:
        """
        Détermine si une requête provenant de l'identifiant (ex: IP) est autorisée.
        Retourne True si dans la limite, False en cas de dépassement.
        """
        now = time.time()
        window_start = now - 60.0  # Fenêtre de 60 secondes

        with self._lock:
            self._cleanup_expired(now)

            timestamps = self._records[identifier]
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
            self._last_cleanup = time.time()


# Instance globale partagée
_rate_limiter = InMemoryRateLimiter()


def get_rate_limiter() -> InMemoryRateLimiter:
    return _rate_limiter
