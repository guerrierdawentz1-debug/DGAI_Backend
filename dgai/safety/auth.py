"""
dgai.safety.auth — Gestion de l'authentification, hachage de mots de passe et jetons JWT via PyJWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    ImmatureSignatureError,
    InvalidAlgorithmError,
    InvalidSignatureError,
    InvalidTokenError,
    PyJWTError,
)
from pydantic import BaseModel
from dgai.core.config import get_settings
from dgai.safety.permissions import Role, Permission, has_permission

# Tolérance maximale de décalage d'horloge (clock skew) en secondes
CLOCK_SKEW_TOLERANCE_SECONDS = 60
# Durée de vie maximale absolue autorisée pour un jeton JWT (24 heures)
MAX_TOKEN_LIFESPAN_SECONDS = 24 * 3600
# Algorithme strictement imposé
ALLOWED_JWT_ALGORITHMS = ["HS256"]


class TokenData(BaseModel):
    """Payload typé et validé extrait d'un jeton JWT."""
    sub: str
    role: Role = Role.USER
    exp: Optional[int] = None
    permissions: list[str] = []


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie la concordance entre un mot de passe en clair et son empreinte bcrypt."""
    if isinstance(plain_password, str):
        password_bytes = plain_password.encode("utf-8")
    else:
        password_bytes = plain_password

    if isinstance(hashed_password, str):
        hash_bytes = hashed_password.encode("utf-8")
    else:
        hash_bytes = hashed_password

    return bcrypt.checkpw(password_bytes, hash_bytes)


def get_password_hash(password: str) -> str:
    """Génère l'empreinte bcrypt sécurisée d'un mot de passe."""
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    else:
        password_bytes = password

    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_access_token(
    subject: str,
    role: Role = Role.USER,
    expires_delta: Optional[timedelta] = None,
    custom_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Génère un jeton JWT signé avec expiration et rôle assigné en utilisant PyJWT.
    Vérifie que la durée de vie n'excède pas la limite maximale autorisée (24h).
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)

    if expires_delta:
        if expires_delta.total_seconds() > MAX_TOKEN_LIFESPAN_SECONDS:
            raise ValueError(f"La durée de vie du jeton excède le maximum autorisé ({MAX_TOKEN_LIFESPAN_SECONDS}s).")
        expire = now + expires_delta
    else:
        expire_minutes = min(settings.jwt_access_token_expire_minutes, 1440)
        expire = now + timedelta(minutes=expire_minutes)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role.value,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    if custom_claims:
        to_encode.update(custom_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    """
    Décode, vérifie la signature et la validité temporelle d'un jeton JWT avec PyJWT.
    - Exige impérativement une date d'expiration ('exp') et de création ('iat').
    - Interdit formellement l'algorithme 'none' et tout algorithme différent de HS256.
    - Vérifie la tolérance d'horloge (max 60s) et le plafond de durée de vie (24h).
    - Lève ValueError avec message générique sécurisé si le jeton est invalide ou expiré.
    """
    if not token or not isinstance(token, str) or not token.strip():
        raise ValueError("Le jeton fourni est vide ou invalide.")

    settings = get_settings()

    try:
        # Inspection préalable du header sans faire confiance à l'algorithme
        unverified_headers = jwt.get_unverified_header(token)
        alg = unverified_headers.get("alg")

        if not alg or alg.lower() == "none" or alg != settings.jwt_algorithm:
            raise ValueError(f"Algorithme de jeton non autorisé ou discordant : '{alg}' (Attendu : {settings.jwt_algorithm})")

        # Décodage et vérification stricte via PyJWT
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=ALLOWED_JWT_ALGORITHMS,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "require": ["exp", "iat", "sub"],
            },
            leeway=CLOCK_SKEW_TOLERANCE_SECONDS
        )

        subject: str = payload.get("sub")
        if not subject or not isinstance(subject, str) or not subject.strip():
            raise ValueError("Le jeton ne contient pas d'identifiant sujet ('sub') valide.")

        exp: int = payload.get("exp")
        iat: int = payload.get("iat")

        now_ts = int(datetime.now(timezone.utc).timestamp())

        # Vérifier la cohérence temporelle
        if iat > now_ts + CLOCK_SKEW_TOLERANCE_SECONDS:
            raise ValueError(f"Date d'émission 'iat' située dans le futur au-delà de la tolérance ({CLOCK_SKEW_TOLERANCE_SECONDS}s).")

        if exp < iat:
            raise ValueError("Le jeton comporte une date d'expiration antérieure à sa date d'émission.")

        if exp - iat > MAX_TOKEN_LIFESPAN_SECONDS:
            raise ValueError(f"La durée de validité du jeton ({exp - iat}s) dépasse la limite maximale ({MAX_TOKEN_LIFESPAN_SECONDS}s).")

        role_str: str = payload.get("role", Role.USER.value)
        try:
            role = Role(role_str)
        except ValueError:
            role = Role.USER

        return TokenData(sub=subject, role=role, exp=exp)

    except ExpiredSignatureError as e:
        raise ValueError(f"Jeton expiré : {str(e)}") from e
    except (InvalidSignatureError, InvalidAlgorithmError, InvalidTokenError, PyJWTError) as e:
        raise ValueError(f"Jeton invalide ou signature incorrecte : {str(e)}") from e
    except Exception as e:
        raise ValueError(f"Jeton invalide : {str(e)}") from e
