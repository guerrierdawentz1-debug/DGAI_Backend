# DGAI — Confidentialité, Rétention et Contrôle Utilisateur

## 1. Principes de Confidentialité

DGAI applique une politique stricte empêchant la mémorisation durable d'informations critiques :
- **Rejet automatique** : Tout contenu contenant des mots de passe, des identifiants bancaires, des clés d'API privées ou des jetons JWT lève immédiatement une exception `PrivacyViolationError` (`HTTP 400`).
- **Isolation propriétaire stricte** : Aucun utilisateur ne peut accéder aux conversations ou aux souvenirs d'un tiers. Les requêtes non autorisées renvoient `HTTP 404 Not Found` sans divulguer l'existence de la ressource.

---

## 2. Rétention et Droit à l'Oubli (RGPD)

- **Date d'expiration** : Calculée à la création selon `DGAI_MEMORY_RETENTION_DAYS`. Les mémoires expirées sont automatiquement ignorées lors de la recherche.
- **Suppression définitive** : L'endpoint `DELETE /api/v1/memories/{memory_id}` exécute une suppression physique immédiate (`DELETE FROM long_term_memories`).
- **Suppression de conversation** : L'endpoint `DELETE /api/v1/conversations/{conversation_id}` purge par cascade l'ensemble des messages, résumés et états de session rattachés.
- **Droit à l'oubli complet** : Méthode `delete_all_user_memories(user_id)` permettant la purge totale sur demande.
