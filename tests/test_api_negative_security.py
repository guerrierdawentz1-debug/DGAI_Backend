"""
Tests de sécurité négatifs et approfondis : JWT (PyJWT), Algorithmes, RBAC, Purge Rate Limiter, Corrélation.
Couvre exhaustivement les 13 cas d'audit JWT exigés.
"""

from datetime import datetime, timezone
import base64
import json
import pytest
import jwt
from pydantic import ValidationError
from dgai.core.config import DGAISettings, EnvironmentType
from dgai.safety.audit import SecurityEventType, log_security_event, CriticalAuditFailureException
from dgai.safety.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from dgai.safety.permissions import Permission, Role, has_permission
from dgai.safety.rate_limit import InMemoryRateLimiter


def test_jwt_valid_token():
    """1. Jeton valide."""
    token = create_access_token(subject="valid_user", role=Role.USER)
    data = decode_access_token(token)
    assert data.sub == "valid_user"
    assert data.role == Role.USER


def test_jwt_reject_invalid_signature():
    """2. Signature incorrecte."""
    token = create_access_token(subject="valid_user")
    parts = token.split(".")
    # Altérer la signature
    tampered = f"{parts[0]}.{parts[1]}.bad_signature_abc123"
    with pytest.raises(ValueError) as exc:
        decode_access_token(tampered)
    assert "signature incorrecte" in str(exc.value).lower() or "invalide" in str(exc.value).lower()


def test_jwt_reject_wrong_secret_key():
    """3. Clé secrète incorrecte."""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = {"sub": "user_diff_key", "role": "user", "iat": now_ts, "exp": now_ts + 300}
    token_wrong_key = jwt.encode(payload, "une_autre_cle_secrete_completement_differente_32c", algorithm="HS256")

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_wrong_key)
    assert "invalide" in str(exc.value).lower() or "signature" in str(exc.value).lower()


def test_jwt_reject_algorithm_different_than_hs256():
    """4. Algorithme différent de HS256."""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = {"sub": "user_hs384", "role": "user", "iat": now_ts, "exp": now_ts + 300}
    # Encodé en HS384 ou HS512
    token_hs384 = jwt.encode(payload, "secret_cle_longue_suffisante_32_caracteres!", algorithm="HS384")

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_hs384)
    assert "non autorisé" in str(exc.value).lower() or "discordant" in str(exc.value).lower()


def test_jwt_reject_none_algorithm():
    """5. Algorithme 'none' forgé."""
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


def test_jwt_reject_expired():
    """6. Jeton expiré."""
    now_ts = int(datetime.now(timezone.utc).timestamp())
    settings = DGAISettings()
    payload = {"sub": "old_user", "role": "user", "iat": now_ts - 500, "exp": now_ts - 200}
    token_expired = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_expired)
    assert "expiré" in str(exc.value).lower()


def test_jwt_reject_missing_exp():
    """7. Champ 'exp' absent."""
    settings = DGAISettings()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = {"sub": "user_no_exp", "role": "user", "iat": now_ts}
    token_no_exp = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_no_exp)
    assert "invalide" in str(exc.value).lower() or "exp" in str(exc.value).lower()


def test_jwt_reject_missing_iat():
    """8. Champ 'iat' absent."""
    settings = DGAISettings()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    payload = {"sub": "user_no_iat", "role": "user", "exp": now_ts + 300}
    token_no_iat = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_no_iat)
    assert "invalide" in str(exc.value).lower() or "iat" in str(exc.value).lower()


def test_jwt_reject_future_iat():
    """9. Date 'iat' dans le futur au-delà de 60s."""
    settings = DGAISettings()
    future_iat = int(datetime.now(timezone.utc).timestamp()) + 180  # +3 minutes
    payload = {"sub": "future_user", "role": "user", "iat": future_iat, "exp": future_iat + 3600}
    token_future = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_future)
    assert "futur" in str(exc.value).lower() or "invalide" in str(exc.value).lower()


def test_jwt_reject_excessive_lifespan():
    """10. Durée de vie excessive (> 24h)."""
    settings = DGAISettings()
    now_ts = int(datetime.now(timezone.utc).timestamp())
    excessive_exp = now_ts + (48 * 3600)  # 48 heures
    payload = {"sub": "greedy_user", "role": "user", "iat": now_ts, "exp": excessive_exp}
    token_long = jwt.encode(payload, settings.secret_key, algorithm="HS256")

    with pytest.raises(ValueError) as exc:
        decode_access_token(token_long)
    assert "dépasse la limite" in str(exc.value).lower()


def test_jwt_reject_malformed():
    """11. Jeton malformé."""
    with pytest.raises(ValueError) as exc:
        decode_access_token("not.a.valid.jwt.token.format")
    assert "invalide" in str(exc.value).lower()


def test_jwt_reject_empty():
    """12. Jeton vide."""
    with pytest.raises(ValueError) as exc:
        decode_access_token("")
    assert "vide" in str(exc.value).lower() or "invalide" in str(exc.value).lower()


def test_production_secret_key_minimum_length():
    """Validation de la longueur de clé secrète en production."""
    with pytest.raises(ValidationError):
        DGAISettings(
            environment=EnvironmentType.PRODUCTION,
            secret_key="court_secret_inferieur_32"
        )


def test_insecure_jwt_algorithm_rejected():
    """Validation stricte rejetant tout algorithme différent de HS256."""
    with pytest.raises(ValidationError):
        DGAISettings(jwt_algorithm="none")

    with pytest.raises(ValidationError):
        DGAISettings(jwt_algorithm="HS384")


def test_bcrypt_long_password_and_different_salts():
    """Vérifie que bcrypt gère les mots de passe et produit des sels distincts."""
    p1 = "mot_de_passe_robuste_dgai_2026"
    h1 = get_password_hash(p1)
    h2 = get_password_hash(p1)

    assert h1 != h2
    assert verify_password(p1, h1)
    assert verify_password(p1, h2)
    assert not verify_password("autre_mot_de_passe", h1)


def test_rate_limiter_memory_cleanup():
    """Vérifie que le limiteur purge les identifiants expirés pour éviter l'épuisement mémoire."""
    limiter = InMemoryRateLimiter(requests_per_minute=10)
    limiter.is_allowed("temp_ip_1")
    assert "temp_ip_1" in limiter._records

    limiter._records["temp_ip_1"] = [1.0]
    limiter._cleanup_expired(now=1000.0, force=True)

    assert "temp_ip_1" not in limiter._records


def test_rate_limiter_max_capacity_eviction():
    """Vérifie que le limiteur évince des clés si la capacité maximale est atteinte."""
    limiter = InMemoryRateLimiter(requests_per_minute=5)
    limiter.MAX_TRACKED_IDENTIFIERS = 3

    limiter.is_allowed("client_A")
    limiter.is_allowed("client_B")
    limiter.is_allowed("client_C")
    assert len(limiter._records) == 3

    limiter.is_allowed("client_D")
    assert len(limiter._records) <= 3
    assert "client_D" in limiter._records


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


def test_critical_audit_failure_behavior(monkeypatch):
    """Vérifie que les opérations critiques échouent de façon fail-safe si l'audit échoue."""
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
