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

python3 main.py
