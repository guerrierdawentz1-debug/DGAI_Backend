"""
dgai.core.logging — Système de journalisation structurée (JSON / Texte).

Assure une traçabilité complète des événements système, sans jamais logger
de données sensibles, avec enrichissement contextuel (timestamp, niveau, module).
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict
from dgai.core.config import LogFormat, get_settings


class StructuredJsonFormatter(logging.Formatter):
    """
    Formateur de logs produisant du JSON structuré conforme aux standards
    de production et d'observabilité.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # Enrichissement avec les métadonnées contextuelles éventuelles
        if hasattr(record, "context") and isinstance(record.context, dict):
            log_payload["context"] = record.context

        # Gestion des traces d'exceptions si présentes
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload, ensure_ascii=False)


def setup_logging(
    level: str | None = None,
    log_format: LogFormat | None = None
) -> logging.Logger:
    """
    Configure la journalisation racine et retourne le logger principal DGAI.
    """
    settings = get_settings()
    target_level = level or settings.log_level
    target_format = log_format or settings.log_format

    root_logger = logging.getLogger("dgai")
    root_logger.setLevel(target_level.upper())

    # Nettoyage des handlers existants pour éviter les duplications
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(target_level.upper())

    if target_format == LogFormat.JSON:
        formatter = StructuredJsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s (%(module)s:%(lineno)d): %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.propagate = False

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Retourne un logger nommé dans l'espace de nom 'dgai.*'.
    """
    if name == "dgai" or name.startswith("dgai."):
        return logging.getLogger(name)
    return logging.getLogger(f"dgai.{name}")
