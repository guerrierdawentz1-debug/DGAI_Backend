# DGAI — Documentation de l'API REST FastAPI

## Vue d'ensemble

L'API DGAI est construite avec **FastAPI** et **Pydantic v2**. Elle implémente une défense en profondeur :
- Validation stricte des requêtes entrantes.
- En-têtes de sécurité conformes aux recommandations OWASP.
- Limitation de taille de corps de requête (`max_request_size_bytes`).
- Limitation de débit de requêtes par IP (`rate_limit_requests_per_minute`).
- Authentification par jetons signés JWT via **PyJWT** (strictement HS256) avec contrôle d'accès basé sur les rôles (RBAC).
- Assainissement des données d'audit avec caviardage automatique des PII et des clés secrètes.

---

## Points de Terminaison Implémentés (Phase 2)

### 1. Santé du Service

- **`GET /health`**
  - **Accès** : Public (sans authentification).
  - **Description** : Retourne l'état de fonctionnement et la version de l'application sans données sensibles.
  - **Exemple de réponse** :
    ```json
    {
      "status": "healthy",
      "app_name": "DGAI Core",
      "version": "0.1.0",
      "environment": "development",
      "timestamp": "2026-10-31T20:57:28.830962+00:00"
    }
    ```

---

### 2. Authentification et Délivrance de Jetons

- **`POST /api/v1/auth/token`**
  - **Accès** : Public (attribué sous restrictions de rôle).
  - **Corps de requête** :
    ```json
    {
      "client_id": "mon_application",
      "requested_role": "user"
    }
    ```
  - **Exemple de réponse** :
    ```json
    {
      "success": true,
      "message": "Jeton généré avec succès.",
      "data": {
        "access_token": "eyJhbGciOiJIUzI1Ni...",
        "token_type": "bearer",
        "expires_in_minutes": 60,
        "role": "user"
      },
      "timestamp": "..."
    }
    ```

---

### 3. Informations Système

- **`GET /api/v1/system/info`**
  - **Accès** : Protégé (Nécessite le header `Authorization: Bearer <token>` avec permission `read:system_info`).
  - **Description** : Retourne les caractéristiques non sensibles de l'instance DGAI en cours d'exécution.
  - **Exemple de réponse** :
    ```json
    {
      "success": true,
      "message": "Informations système récupérées avec succès.",
      "data": {
        "app_name": "DGAI Core",
        "version": "0.1.0",
        "environment": "development",
        "python_version": "3.12.13",
        "api_prefix": "/api/v1",
        "docs_enabled": true,
        "active_features": [
          "Phase 1: Foundations",
          "Phase 2: Security & API Gateway"
        ],
        "rate_limit_per_minute": 60
      },
      "timestamp": "..."
    }
    ```

---

## Fonctionnalités Non Encore Implémentées (Réservées aux phases ultérieures)

Les routes suivantes **ne sont pas encore implémentées** et ne doivent pas être appelées avant leurs phases respectives :
- Inférence LLM (`/api/v1/predict`, `/api/v1/chat`) -> Réservé à la Phase 3.
- Raisonnement & Planification (`/api/v1/reasoning`) -> Réservé à la Phase 4.
- Mémoire & Recherche documentaire (`/api/v1/memory`, `/api/v1/rag`) -> Réservé à la Phase 5.
- Recherche Web (`/api/v1/search`) -> Réservé à la Phase 6.
- Agents & Sandbox (`/api/v1/agents`, `/api/v1/tools`) -> Réservé aux Phases 7 et 8.
