#!/usr/bin/env bash
set -euo pipefail

echo "================================================="
echo "DGAI — Lancement de l'environnement de développement"
echo "================================================="

export DGAI_ENVIRONMENT="development"
export DGAI_DEBUG="true"

if [ -f .env ]; then
    echo "Chargement du fichier .env existant..."
else
    echo "Création d'un .env depuis .env.example..."
    cp .env.example .env
fi

python3 -c "from dgai.core.config import get_settings; from dgai.core.logging import setup_logging; setup_logging(); s = get_settings(); print(f'DGAI prêt en mode {s.environment.value} sur {s.host}:{s.port}')"
