"""
Tests unitaires pour dgai.core.config (Pydantic Settings et validations).
"""

import os
import pytest
from pydantic import ValidationError
from dgai.core.config import DGAISettings, EnvironmentType, LogFormat, get_settings, reset_settings


def test_default_settings(monkeypatch):
    """Vérifie que les paramètres par défaut sont valides et cohérents."""
    # S'assurer qu'aucune variable DGAI_* de l'environnement n'altère le test par défaut
    for key in list(os.environ.keys()):
        if key.startswith("DGAI_"):
            monkeypatch.delenv(key, raising=False)

    settings = DGAISettings()
    assert settings.environment == EnvironmentType.DEVELOPMENT
    assert settings.debug is False
    assert settings.app_name == "DGAI Core"
    assert settings.port == 8000
    assert settings.host == "127.0.0.1"
    assert settings.log_level == "INFO"
    assert settings.log_format == LogFormat.JSON
    assert settings.sandbox_timeout_seconds == 5.0
    assert settings.sandbox_network_enabled is False


def test_custom_environment_settings(monkeypatch):
    """Vérifie la surcharge des paramètres via les variables d'environnement."""
    monkeypatch.setenv("DGAI_ENVIRONMENT", "test")
    monkeypatch.setenv("DGAI_DEBUG", "true")
    monkeypatch.setenv("DGAI_PORT", "9000")
    monkeypatch.setenv("DGAI_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DGAI_LOG_FORMAT", "text")
    monkeypatch.setenv("DGAI_SANDBOX_TIMEOUT_SECONDS", "10.5")

    settings = DGAISettings()
    assert settings.environment == EnvironmentType.TEST
    assert settings.debug is True
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"
    assert settings.log_format == LogFormat.TEXT
    assert settings.sandbox_timeout_seconds == 10.5


def test_invalid_log_level():
    """Vérifie qu'un niveau de log invalide lève une ValidationError."""
    with pytest.raises(ValidationError):
        DGAISettings(log_level="SUPER_CRITICAL_INVALID")


def test_production_secret_key_rejection():
    """Vérifie qu'une clé de développement par défaut est interdite en production."""
    with pytest.raises(ValidationError) as exc_info:
        DGAISettings(
            environment=EnvironmentType.PRODUCTION,
            secret_key="dgai-insecure-default-development-key"
        )
    assert "PRODUCTION" in str(exc_info.value)


def test_production_with_secure_secret():
    """Vérifie qu'une clé personnalisée en production est autorisée."""
    settings = DGAISettings(
        environment=EnvironmentType.PRODUCTION,
        secret_key="super_secure_production_secret_key_123"
    )
    assert settings.environment == EnvironmentType.PRODUCTION
    assert settings.secret_key == "super_secure_production_secret_key_123"


def test_settings_singleton_and_reset():
    """Vérifie le fonctionnement de get_settings et reset_settings."""
    reset_settings()
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2

    custom_s = DGAISettings(app_name="DGAI Custom Test")
    reset_settings(custom_s)
    assert get_settings().app_name == "DGAI Custom Test"

    reset_settings()
