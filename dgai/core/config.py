"""
dgai.core.config — Configuration typée et immuable basée sur Pydantic Settings.

Ce module gère le chargement transparent des paramètres depuis l'environnement,
les fichiers .env et applique des règles strictes de validation.
"""

from enum import Enum
from pathlib import Path
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class LogFormat(str, Enum):
    JSON = "json"
    TEXT = "text"


class DGAISettings(BaseSettings):
    """
    Paramètres globaux du projet DGAI.
    Tous les champs sont typés et validés automatiquement.
    """
    model_config = SettingsConfigDict(
        env_prefix="DGAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    # Environnement & Cycle de vie
    environment: EnvironmentType = Field(
        default=EnvironmentType.DEVELOPMENT,
        description="Type d'environnement d'exécution"
    )
    debug: bool = Field(
        default=False,
        description="Mode débogage actif ou inactif"
    )

    # Identité du service
    app_name: str = Field(
        default="DGAI Core",
        description="Nom de l'application"
    )
    app_version: str = Field(
        default="0.1.0",
        description="Version sémantique de l'application"
    )

    # Réseau & Serveur
    host: str = Field(
        default="127.0.0.1",
        description="Adresse IP d'écoute"
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Port d'écoute TCP"
    )

    # Journalisation
    log_level: str = Field(
        default="INFO",
        description="Niveau de journalisation standard (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_format: LogFormat = Field(
        default=LogFormat.JSON,
        description="Format de sortie des journaux (json ou text)"
    )

    # Chemins de stockage
    data_dir: Path = Field(
        default=Path("./data"),
        description="Répertoire local de stockage des données"
    )
    models_dir: Path = Field(
        default=Path("./models"),
        description="Répertoire des modèles légers (poids lourds exclus de Git)"
    )
    checkpoints_dir: Path = Field(
        default=Path("./checkpoints"),
        description="Répertoire des sauvegardes de checkpoints"
    )

    # Sécurité
    secret_key: str = Field(
        default="dgai-insecure-default-development-key",
        description="Clé secrète pour les signatures et jetons"
    )
    allowed_hosts: List[str] = Field(
        default_factory=lambda: ["127.0.0.1", "localhost"],
        description="Hôtes autorisés pour les requêtes entrantes"
    )

    # Sandbox & Sécurité d'exécution
    sandbox_timeout_seconds: float = Field(
        default=5.0,
        ge=0.1,
        le=300.0,
        description="Délai maximum d'exécution d'un processus sandbox"
    )
    sandbox_max_memory_mb: int = Field(
        default=512,
        ge=64,
        le=8192,
        description="Limite maximale de mémoire RAM par conteneur/process sandbox"
    )
    sandbox_network_enabled: bool = Field(
        default=False,
        description="Désactivation du réseau par défaut pour la sandbox"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Niveau de log invalide: '{v}'. Niveaux valides: {valid_levels}")
        return upper_v

    @field_validator("secret_key")
    @classmethod
    def validate_production_secret(cls, v: str, info) -> str:
        env = info.data.get("environment")
        if env == EnvironmentType.PRODUCTION and v == "dgai-insecure-default-development-key":
            raise ValueError(
                "La clé secrète par défaut ne peut PAS être utilisée dans un environnement de PRODUCTION."
            )
        return v


# Instance singleton ou fonction factory pour un accès contrôlé
_settings_instance: DGAISettings | None = None


def get_settings() -> DGAISettings:
    """Retourne l'instance unique ou courante des paramètres DGAI."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = DGAISettings()
    return _settings_instance


def reset_settings(new_settings: DGAISettings | None = None) -> None:
    """Réinitialise ou remplace la configuration courante (notamment pour les tests)."""
    global _settings_instance
    _settings_instance = new_settings
