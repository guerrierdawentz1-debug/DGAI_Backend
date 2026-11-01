# DGAI — Gestion Intelligente de la Fenêtre de Contexte

## 1. Vue d'ensemble

Le module `dgai.reasoning.context.ContextManager` prépare et assemble les informations transmises au modèle LLM sans dépasser sa fenêtre de contexte maximale.

---

## 2. Cycle d'Assemblage

1. **Instructions Système** : Consignes primaires inaltérables placées en tête.
2. **Faits Mémorisés Pertinents** : Injectés comme données externes non-privilégiées.
3. **Résumé de Conversation** : Intégré si présent et si le budget le permet.
4. **Messages Récents** : Sélectionnés de manière antéchronologique puis remis dans l'ordre chronologique. Les messages trop anciens sont élagués de façon traçable (`pruned_messages_count`).
5. **Marge Réservée** : Quota garanti (`context_reserve_tokens`) pour la génération de la réponse.

---

## 3. Estimation des Tokens

- Méthode : `estimate_tokens(text) -> int` basée sur un ratio conservateur d'environ 4 caractères par token pour les langues latines.
- Documentation explicite : Indiqué comme approximation conservative tant qu'un tokenizer BPE spécifique au modèle n'est pas instancié.
