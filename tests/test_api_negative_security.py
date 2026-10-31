"""
Tests de sécurité négatifs et approfondis : JWT, Algorithmes, RBAC, Purge Rate Limiter, Corrélation.
"""

from datetime import datetime, timezone
import pytest
from jose import jwt
from pydantic import ValidationError
from dgai.core.config import DGAISettings, EnvironmentType
from dgai.safety.audit import SecurityEventType, log_security_event
from dgai.safety.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from dgai.safety.permissions import Permission, Role, has_permission
from dgai.safety.rate_limit import InMemoryRateLimiter


import base64
import json

def test_jwt_reject_none_algorithm():
    """Vérifie le rejet formel des jetons forgés avec alg=none (vulnérabilité classique)."""
    header = {"alg": "none", "typ": "JWT"}
    payload = {
        "sub": "attacker",
        "role": "admin",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(datetime.now(timezone.utc).timestamp()) + 3600
    }
    encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b'=').decode()
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b'=').decode()
    token_none = f"{encoded_header}.{encoded_payload}."

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_none)
    assert "non autorisé" in str(exc.value).lower() or "discordant" in str(exc.value).lower()


def test_jwt_reject_missing_expiration():
    """Vérifie le rejet d'un jeton valide cryptographiquement mais dépourvu d'expiration 'exp'."""
    settings = DGAISettings()
    payload = {"sub": "eternal_user", "role": "user", "iat": int(datetime.now(timezone.utc).timestamp())}
    token_no_exp = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_no_exp)
    assert "exp" in str(exc.value).lower()


def test_jwt_reject_empty_or_whitespace_subject():
    """Vérifie le rejet d'un jeton avec un sujet vide ou constitué d'espaces."""
    token_empty = create_access_token(subject="   ")
    with pytest.raises(ValueError) as exc:
        decode_access_token(token_empty)
    assert "sujet" in str(exc.value).lower() or "sub" in str(exc.value).lower()


def test_jwt_reject_exp_before_iat():
    """Vérifie le rejet d'un jeton dont l'expiration précède la date d'émission."""
    settings = DGAISettings()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = {"sub": "time_traveler", "role": "user", "iat": now_ts, "exp": now_ts - 500}
    token_inconsistent = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(ValueError):
        decode_access_token(token_inconsistent)


def test_production_secret_key_minimum_length():
    """Vérifie qu'en production, une clé de moins de 32 caractères est refusée."""
    with pytest.raises(ValidationError):
        DGAISettings(
            environment=EnvironmentType.PRODUCTION,
            secret_key="court_secret_inferieur_32"
        )


def test_insecure_jwt_algorithm_rejected():
    """Vérifie le rejet d'algorithmes faibles dans la configuration."""
    with pytest.raises(ValidationError):
        DGAISettings(jwt_algorithm="none")

    with pytest.raises(ValidationError):
        DGAISettings(jwt_algorithm="MD5")


def test_bcrypt_long_password_and_different_salts():
    """Vérifie que bcrypt gère les mots de passe et produit des sels distincts."""
    p1 = "mot_de_passe_robuste_dgai_2026"
    h1 = get_password_hash(p1)
    h2 = get_password_hash(p1)

    assert h1 != h2  # Sels différents
    assert verify_password(p1, h1)
    assert verify_password(p1, h2)
    assert not verify_password("autre_mot_de_passe", h1)


def test_rate_limiter_memory_cleanup():
    """Vérifie que le limiteur purge les identifiants expirés pour éviter l'épuisement mémoire."""
    limiter = InMemoryRateLimiter(requests_per_minute=10)
    limiter.is_allowed("temp_ip_1")
    assert "temp_ip_1" in limiter._records

    # Simuler le passage du temps (plus de 65s) avec purge forcée
    limiter._records["temp_ip_1"] = [1.0]  # Timestamp très ancien
    limiter._cleanup_expired(now=1000.0, force=True)

    assert "temp_ip_1" not in limiter._records


def test_audit_event_correlation_id_and_failsafe():
    """Vérifie la génération d'un correlation_id et l'assainissement systématique."""
    event = log_security_event(
        event_type=SecurityEventType.AUTH_FAILURE,
        client_ip="192.168.1.1",
        endpoint="/test",
        actor="untrusted",
        details={"token": "eyJhbGciOi.eyJzdWIi.secret", "password": "clear_password"},
        correlation_id="test-cid-999"
    )

    assert event["correlation_id"] == "test-cid-999"
    assert event["details"]["password"] == "[REDACTED]"
    assert event["details"]["token"] == "[REDACTED]"


def test_jwt_reject_future_iat():
    """Vérifie le rejet d'un jeton dont la date 'iat' est située dans le futur au delà de 60s."""
    settings = DGAISettings()
    future_iat = int(datetime.now(timezone.utc).timestamp()) + 120  # +2 minutes
    payload = {"sub": "future_user", "role": "user", "iat": future_iat, "exp": future_iat + 3600}
    token_future = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_future)
    assert "futur" in str(exc.value).lower()


def test_jwt_reject_excessive_lifespan():
    """Vérifie le rejet d'un jeton dont la validité dépasse la limite maximale absolue de 24h."""
    settings = DGAISettings()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    excessive_exp = now_ts + (48 * 3600)  # 48 heures
    payload = {"sub": "greedy_user", "role": "user", "iat": now_ts, "exp": excessive_exp}
    token_long = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_long)
    assert "dépasse la limite" in str(exc.value).lower()


def test_rate_limiter_max_capacity_eviction():
    """Vérifie que le limiteur évince des clés si la capacité maximale de 10 000 est atteinte."""
    limiter = InMemoryRateLimiter(requests_per_minute=5)
    limiter.MAX_TRACKED_IDENTIFIERS = 3  # Réduire temporairement le seuil pour le test

    limiter.is_allowed("client_A")
    limiter.is_allowed("client_B")
    limiter.is_allowed("client_C")
    assert len(limiter._records) == 3

    # Ajout d'un 4ème client -> doit évincer le plus ancien sans crasher
    limiter.is_allowed("client_D")
    assert len(limiter._records) <= 3
    assert "client_D" in limiter._records


def test_critical_audit_failure_behavior(monkeypatch):
    """Vérifie que les opérations critiques échouent de façon fail-safe si l'audit échoue."""
    from dgai.safety.audit import CriticalAuditFailureException
    import dgai.safety.audit

    def broken_log(*args, **kwargs):
        raise IOError("Disque plein ou indisponible")

    monkeypatch.setattr(dgai.safety.audit.audit_logger, "warning", broken_log)

    with pytest.raises(CriticalAuditFailureException):
        log_security_event(
            event_type=SecurityEventType.ACCESS_DENIED,
            client_ip="1.2.3.4",
            endpoint="/admin",
            critical=True
        )
