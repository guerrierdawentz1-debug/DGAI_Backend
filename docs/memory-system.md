# DGAI — Système de Mémoire Multi-Couches

## 1. Principes et Couches de Mémoire

DGAI met en œuvre un système de mémoire à 4 couches indépendantes, isolées strictement par utilisateur :

1. **Mémoire de Conversation (Short-Term Memory)** (`dgai.memory.conversation.ConversationManager`) :
   - Historique chronologique exact des échanges (`role: user`, `assistant`).
   - Rattaché à une conversation unique (`conversation_id`).
   - Isolé par `user_id`.
2. **Mémoire à Long Terme (Long-Term Memory)** (`dgai.memory.long_term.LongTermMemoryManager`) :
   - Faits, préférences déclarées et instructions persistantes entre plusieurs conversations.
   - Soumis à la politique de confidentialité (`dgai.memory.policies.privacy`).
   - Rejet systématique des mots de passe, cartes bancaires, clés d'API et jetons JWT.
3. **Mémoire de Travail / Session (Working Memory)** (`dgai.memory.session.SessionManager`) :
   - Sujet actif, objectifs en cours, décisions actées et tâches ouvertes.
4. **Résumé Automatique de Conversation** (`dgai.memory.summarizer.ConversationSummarizer`) :
   - Synthèse structurée déclenchée au-delà d'un seuil de messages.
   - Règle d'intégrité : aucun résumé fictif n'est généré si le modèle réel est indisponible, et les anciens résumés valides sont rigoureusement préservés.

---

## 2. Couche de Stockage SQLite

- **Implémentation** : `dgai.memory.storage.sqlite.SQLiteMemoryStorage`
- **Garanties** :
  - Requêtes strictement paramétrées (protection totale contre les injections SQL).
  - Intégrité référentielle SQLite (`PRAGMA foreign_keys = ON;`) avec suppression en cascade (`ON DELETE CASCADE`).
  - Verrouillage multi-threads `threading.Lock()` pour prévenir les écritures concurrentes corrompues.
  - Toutes les requêtes filtrent obligatoirement par `WHERE user_id = ?`.
