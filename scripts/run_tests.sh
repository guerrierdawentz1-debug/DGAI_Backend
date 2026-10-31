#!/usr/bin/env bash
set -euo pipefail

echo "================================================="
echo "DGAI — Exécution de la suite de tests automatisés"
echo "================================================="

export DGAI_ENVIRONMENT="test"
export DGAI_LOG_LEVEL="WARNING"

python3 -m pytest -v "$@"
