"""
dgai.api.app — Application FastAPI principale et configuration des middlewares / exceptions.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from dgai.api.exceptions import (
    DGAIAPIException,
    dgai_api_exception_handler,
    generic_exception_handler,
    validation_exception_handler,
)
from dgai.api.middleware import (
    RateLimitMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from dgai.api.routes.health import router as health_router
from dgai.api.routes.v1 import v1_router
from dgai.core.config import EnvironmentType, get_settings
from dgai.core.logging import get_logger, setup_logging

logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cycle de vie de l'application FastAPI (Démarrage et Arrêt)."""
    settings = get_settings()
    setup_logging()
    logger.info(
        f"Initialisation de l'API {settings.app_name} (v{settings.app_version}) en mode {settings.environment.value}"
    )
    yield
    logger.info("Arrêt propre de l'API DGAI.")


def create_app() -> FastAPI:
    """
    Factory construisant et configurant l'application FastAPI avec toutes ses sécurités.
    """
    settings = get_settings()

    # Documentation Swagger/OpenAPI accessible selon la configuration
    docs_url = "/docs" if settings.enable_docs else None
    redoc_url = "/redoc" if settings.enable_docs else None
    openapi_url = "/openapi.json" if settings.enable_docs else None

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="DGAI — Architecture d'Assistant IA Ouvert et Indépendant",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # 1. Middlewares de sécurité (ordre d'application ascendant)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestSizeLimitMiddleware)

    # 2. Middleware CORS avec origines strictement contrôlées
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # 3. Gestionnaires d'exceptions centralisés
    app.add_exception_handler(DGAIAPIException, dgai_api_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # 4. Inclusion des routeurs
    app.include_router(health_router)
    app.include_router(v1_router, prefix=settings.api_prefix)

    return app


app = create_app()
