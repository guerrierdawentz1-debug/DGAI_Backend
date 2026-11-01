"""
Point d'entrée principal de DGAI — Démarrage du serveur Uvicorn ASGI.
"""

import uvicorn
from dgai.api.app import app
from dgai.core.config import get_settings


def main():
    settings = get_settings()
    uvicorn.run(
        "dgai.api.app:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
