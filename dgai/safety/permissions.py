"""
dgai.safety.permissions — Définition des rôles et permissions RBAC pour DGAI.
"""

from enum import Enum
from typing import Set


class Role(str, Enum):
    ANONYMOUS = "anonymous"
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"


class Permission(str, Enum):
    # Système & Santé
    READ_HEALTH = "read:health"
    READ_SYSTEM_INFO = "read:system_info"

    # Inférence & LLM (Phases futures)
    EXECUTE_INFERENCE = "execute:inference"

    # Mémoire & RAG (Phases futures)
    READ_MEMORY = "read:memory"
    WRITE_MEMORY = "write:memory"
    DELETE_MEMORY = "delete:memory"

    # Outils & Sandbox (Phases futures)
    EXECUTE_TOOL = "execute:tool"
    EXECUTE_SANDBOX = "execute:sandbox"

    # Administration
    ADMIN_CONFIG = "admin:config"
    ADMIN_AUDIT = "admin:audit"


# Matrice des rôles et de leurs permissions
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ANONYMOUS: {
        Permission.READ_HEALTH,
    },
    Role.USER: {
        Permission.READ_HEALTH,
        Permission.READ_SYSTEM_INFO,
        Permission.EXECUTE_INFERENCE,
        Permission.READ_MEMORY,
        Permission.WRITE_MEMORY,
    },
    Role.AGENT: {
        Permission.READ_HEALTH,
        Permission.READ_SYSTEM_INFO,
        Permission.EXECUTE_INFERENCE,
        Permission.READ_MEMORY,
        Permission.WRITE_MEMORY,
        Permission.EXECUTE_TOOL,
        Permission.EXECUTE_SANDBOX,
    },
    Role.ADMIN: set(Permission),  # Toutes les permissions
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Vérifie si un rôle possède une permission donnée."""
    allowed = ROLE_PERMISSIONS.get(role, set())
    return permission in allowed
