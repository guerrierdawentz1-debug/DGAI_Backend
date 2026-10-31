# DGAI — Documentation de Sécurité

## Architecture de Sécurité Multi-Couches

DGAI met en œuvre le principe de défense en profondeur à tous les niveaux de l'architecture.

---

## 1. Authentification & Jetons (JWT)

- **Algorithme de Signature** : `HS256` par défaut (clé secrète configurable via `DGAI_SECRET_KEY`).
- **Protection en Production** : La configuration DGAI interdit formellement de démarrer en mode `production` avec la clé de développement par défaut.
- **Expiration** : Durée de vie configurable (`DGAI_JWT_ACCESS_TOKEN_EXPIRE_MINUTES`). Les jetons expirés ou dont la signature est corrompue sont immédiatement rejetés avec un code `401 Unauthorized`.
- **Hachage des Mots de Passe** : Bcrypt direct avec coût de salage dynamique (`rounds=12`).

---

## 2. Contrôle d'Accès Basé sur les Rôles (RBAC)

DGAI définit 4 rôles standards :
1. **`ANONYMOUS`** : Accès restreint uniquement à `/health`.
2. **`USER`** : Consultation des informations système, et futures interactions standard.
3. **`AGENT`** : Exécution contrôlée d'outils et requêtes de mémoire de travail.
4. **`ADMIN`** : Accès complet d'audit et de configuration.

L'auto-attribution du rôle `ADMIN` sur les routes de délivrance de jetons est verrouillée et refusée.

---

## 3. Protection Contre les Injections et les Attaques HTTP

- **Limitation de Taille de Requête** : Rejet immédiat (`413 Content Too Large`) des charges utiles dépassant `DGAI_MAX_REQUEST_SIZE_BYTES` (2 MB par défaut).
- **Limitation de Débit (Rate Limiting)** : Journal glissant sur 60 secondes limitant le nombre d'appels par IP cliente (`DGAI_RATE_LIMIT_REQUESTS_PER_MINUTE`).
  - *Note sur le déploiement* : L'implémentation actuelle repose sur un verrou thread-safe en mémoire. Pour les déploiements multi-noeuds distribués à grande échelle, une couche de stockage partagé (Redis/Valkey) pourra être branchée sans changer l'interface.
- **En-têtes de Sécurité HTTP** :
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- **Politique CORS** : Origines autorisées définies de manière explicite via `DGAI_CORS_ALLOWED_ORIGINS`.

---

## 4. Protection des Données et Audit Immuable

- **Détection PII & Caviardage Automatique** : Le module `dgai.safety.sanitizer` masque systématiquement les emails (`[REDACTED_EMAIL]`), numéros de téléphone (`[REDACTED_PHONE]`), clés d'API et jetons JWT avant enregistrement dans les journaux d'audit.
- **Protection contre les fuites d'erreurs** : Les exceptions internes retournent une enveloppe d'erreur générique `500 Internal Server Error` sans jamais exposer de trace de pile Python (stacktrace) ni d'information d'infrastructure à l'appelant externe.
