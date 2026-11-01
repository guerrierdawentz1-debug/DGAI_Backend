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

---

### 4. Inférence et Chat (Phase 3)

- **`POST /api/v1/chat`**
  - **Accès** : Protégé (Nécessite le header `Authorization: Bearer <token>` avec permission `execute:inference`).
  - **Corps de requête** :
    ```json
    {
      "messages": [
        {"role": "user", "content": "Explique-moi les principes de DGAI."}
      ],
      "model_id": "optional-target-model-id",
      "temperature": 0.7,
      "max_tokens": 512
    }
    ```
  - **Statut si aucun modèle réel n'est chargé** : Retourne `HTTP 503 Service Unavailable` :
    ```json
    {
      "success": false,
      "error": "Le moteur IA de DGAI n'est pas encore opérationnel : aucun modèle n'est disponible ou chargé.",
      "details": [{"code": "HTTP_503", "message": "..."}],
      "timestamp": "..."
    }
    ```

---

### 5. Gestion des Conversations & Mémoires (Phase 4)

- **`POST /api/v1/conversations`** : Crée une nouvelle conversation.
- **`GET /api/v1/conversations`** : Liste les conversations du client.
- **`GET /api/v1/conversations/{id}`** : Récupère le détail d'une conversation (404 si non propriétaire).
- **`DELETE /api/v1/conversations/{id}`** : Supprime la conversation et son historique par cascade.
- **`GET /api/v1/conversations/{id}/messages`** : Récupère les messages d'une conversation.
- **`POST /api/v1/memories`** : Enregistre un fait/préférence à long terme (rejet des mots de passe/secrets).
- **`GET /api/v1/memories`** : Liste les mémoires durables actives.
- **`GET /api/v1/memories/{id}`** : Détail d'une mémoire.
- **`PATCH /api/v1/memories/{id}`** : Mise à jour d'une mémoire.
- **`DELETE /api/v1/memories/{id}`** : Suppression physique définitive d'une mémoire.

---

## Fonctionnalités Non Encore Implémentées (Réservées aux phases ultérieures)

Les modules suivants **ne sont pas encore implémentés** et ne doivent pas être appelés avant leurs phases respectives :
- Recherche documentaire vectorielle & RAG avancé -> Réservé à la Phase 5.
- Recherche Web multi-fournisseurs -> Réservé à la Phase 6.
- Agents autonomes & Outils -> Réservé à la Phase 7.
- Sandbox d'exécution sécurisée -> Réservé à la Phase 8.
