# DGAI Container Image — Sécurisée, non-root, Python 3.12-slim
FROM python:3.12-slim

# Empêcher Python d'écrire des fichiers .pyc et forcer stdout/stderr sans buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DGAI_ENVIRONMENT=production

# Création d'un groupe et utilisateur non-privilégié pour la sécurité
RUN groupadd -g 1001 dgai && \
    useradd -u 1001 -g dgai -s /bin/bash -m dgai

WORKDIR /app

# Installation des dépendances Python minimales
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie du code source et permissions
COPY --chown=dgai:dgai . .

# Passage à l'utilisateur non-privilégié
USER dgai

# Port d'écoute par défaut
EXPOSE 8000

# Commande par défaut (initialisation des fondations DGAI)
CMD ["python", "-c", "from dgai.core.config import get_settings; from dgai.core.logging import setup_logging; setup_logging(); print('DGAI Core Ready:', get_settings().app_name)"]
