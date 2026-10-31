"""
dgai.api.routes — Regroupement des routes racines.
"""

from dgai.api.routes.health import router as health_router

__all__ = ["health_router"]
