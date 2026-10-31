"""
Tests unitaires pour dgai.core.logging (Formateur structuré JSON et configuration).
"""

import io
import json
import logging
from dgai.core.config import LogFormat
from dgai.core.logging import StructuredJsonFormatter, get_logger, setup_logging


def test_structured_json_formatter():
    """Vérifie que StructuredJsonFormatter produit un JSON valide avec les clés attendues."""
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="dgai.test",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Opération de test réussie",
        args=(),
        exc_info=None,
    )
    record.context = {"operation": "init", "user_id": 101}

    formatted_str = formatter.format(record)
    parsed = json.loads(formatted_str)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "dgai.test"
    assert parsed["message"] == "Opération de test réussie"
    assert parsed["line"] == 42
    assert "timestamp" in parsed
    assert parsed["context"] == {"operation": "init", "user_id": 101}


def test_setup_logging_stream():
    """Vérifie la configuration du logger principal et l'écriture sur le stream."""
    stream = io.StringIO()
    logger = setup_logging(level="DEBUG", log_format=LogFormat.JSON)

    # Remplacer temporairement le stream du handler pour capturer la sortie
    logger.handlers[0].stream = stream
    logger.debug("Message de débogage")

    output = stream.getvalue().strip()
    assert output != ""
    parsed = json.loads(output)
    assert parsed["level"] == "DEBUG"
    assert parsed["message"] == "Message de débogage"


def test_get_logger_naming():
    """Vérifie que les sous-loggers respectent le préfixe de namespace dgai."""
    l1 = get_logger("core")
    assert l1.name == "dgai.core"

    l2 = get_logger("dgai.llm")
    assert l2.name == "dgai.llm"
