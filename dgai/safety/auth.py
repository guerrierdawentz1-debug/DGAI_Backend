"""
dgai.safety.auth — Gestion de l'authentification, hachage de mots de passe et jetons JWT.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from dgai.core.config import get_settings
from dgai.safety.permissions import Role, Permission, has_permission

import bcrypt


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
    Génère un jeton JWT signé avec expiration et rôle assigné.
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

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
    Décode, vérifie la signature et la validité temporelle d'un jeton JWT.
    Lève ValueError si le jeton est invalide ou expiré.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        subject: str = payload.get("sub")
        if subject is None:
            raise ValueError("Le jeton ne contient pas de champ 'sub' valide.")

        role_str: str = payload.get("role", Role.USER.value)
        try:
            role = Role(role_str)
        except ValueError:
            role = Role.USER

        exp: Optional[int] = payload.get("exp")
        return TokenData(sub=subject, role=role, exp=exp)

    except JWTError as e:
        raise ValueError(f"Jeton invalide ou expiré : {str(e)}") from e
