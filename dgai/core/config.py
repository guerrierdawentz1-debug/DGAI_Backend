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

    # Sécurité & Authentification (Phase 2)
    secret_key: str = Field(
        default="dgai-insecure-default-development-key",
        min_length=16,
        description="Clé secrète pour les signatures et jetons (longueur minimale 16 caractères en dev, 32 en prod)"
    )
    allowed_hosts: List[str] = Field(
        default_factory=lambda: ["127.0.0.1", "localhost"],
        description="Hôtes autorisés pour les requêtes entrantes"
    )
    cors_allowed_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Liste des origines CORS autorisées"
    )
    enable_docs: bool = Field(
        default=True,
        description="Active ou désactive la documentation Swagger/OpenAPI"
    )
    api_prefix: str = Field(
        default="/api/v1",
        description="Préfixe d'URL de l'API v1"
    )

    # JWT Tokens
    jwt_algorithm: str = Field(
        default="HS256",
        description="Algorithme de signature des jetons JWT (strictement limité à HS256)"
    )
    jwt_access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        le=43200,
        description="Durée de validité des jetons d'accès en minutes"
    )

    # Protection des requêtes & Rate Limiting
    max_request_size_bytes: int = Field(
        default=2 * 1024 * 1024,  # 2 MB par défaut
        ge=1024,
        le=50 * 1024 * 1024,
        description="Taille maximale autorisée pour le corps de la requête en octets"
    )
    rate_limit_requests_per_minute: int = Field(
        default=60,
        ge=1,
        le=10000,
        description="Nombre maximum de requêtes par minute par IP/client"
    )

    # Moteur LLM & Inférence (Phase 3)
    default_llm_engine: str = Field(
        default="none",
        description="Moteur d'exécution LLM par défaut (none, mock, llama_cpp, vllm, transformers)"
    )
    default_model_id: str = Field(
        default="",
        description="Identifiant du modèle par défaut dans le registre"
    )
    max_generation_tokens: int = Field(
        default=2048,
        ge=1,
        le=131072,
        description="Nombre maximal absolu de tokens générables par requête"
    )
    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Température par défaut pour le sampling"
    )
    llm_generation_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=600.0,
        description="Délai d'attente maximal en secondes pour une génération LLM"
    )
    llm_max_concurrent_requests: int = Field(
        default=10,
        ge=1,
        le=1000,
        description="Nombre maximal de requêtes d'inférence exécutées simultanément"
    )
    allow_mock_provider: bool = Field(
        default=True,
        description="Autorise le fournisseur Mock (strictement réservé aux tests et au développement)"
    )
    max_prompt_length_chars: int = Field(
        default=32768,
        ge=10,
        le=500000,
        description="Longueur maximale en caractères pour le texte d'entrée (prompt)"
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

    @field_validator("jwt_algorithm")
    @classmethod
    def validate_jwt_algorithm(cls, v: str) -> str:
        # Restriction stricte à HS256 comme exigé pour éliminer toute confusion d'algorithme
        secure_algorithms = {"HS256"}
        if v.upper() not in secure_algorithms:
            raise ValueError(f"Algorithme JWT non autorisé : '{v}'. L'algorithme imposé est strictement : {secure_algorithms}")
        return v.upper()

    @field_validator("secret_key")
    @classmethod
    def validate_production_secret(cls, v: str, info) -> str:
        env = info.data.get("environment")
        if env == EnvironmentType.PRODUCTION:
            if v == "dgai-insecure-default-development-key":
                raise ValueError(
                    "La clé secrète par défaut ne peut PAS être utilisée dans un environnement de PRODUCTION."
                )
            if len(v) < 32:
                raise ValueError("En environnement de PRODUCTION, la clé secrète doit comporter au moins 32 caractères.")
        return v

    @field_validator("allow_mock_provider")
    @classmethod
    def validate_mock_in_production(cls, v: bool, info) -> bool:
        env = info.data.get("environment")
        if env == EnvironmentType.PRODUCTION and v is True:
            raise ValueError("Le fournisseur Mock ne peut pas être autorisé en environnement de PRODUCTION.")
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
