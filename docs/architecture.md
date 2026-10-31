# DGAI — Documentation Technique d'Architecture

## Principes Directeurs

1. **Indépendance du Cerveau** : DGAI ne dépend pas obligatoirement d'une API externe. Le cerveau LLM est encapsulé par une interface abstraite permettant le chargement de modèles open-weight locaux (Mistral, Llama, Qwen).
2. **Modularité Découplée** : Chaque module (`core`, `llm`, `reasoning`, `memory`, `rag`, `websearch`, `agents`, `sandbox`, `domains`, `safety`, `evaluation`) possède des frontières nettes.
3. **Sécurité en Profondeur** :
   - Isolation stricte des bacs à sable (utilisateur non-root, réseau coupé par défaut, quotas stricts).
   - Protection anti-SSRF et anti-DNS rebinding pour la recherche web.
   - Défense contre les injections de prompt directes et indirectes.
   - Caviardage automatique des PII et des clés secrètes.
4. **4 Niveaux de Mémoire** :
   - *Short-Term Memory* : Fenêtre de contexte conversationnelle immédiate.
   - *Working Memory* : État d'exécution de l'agent en cours.
   - *Long-Term Memory* : Faits persistants validés par l'utilisateur (droit à l'effacement).
   - *Document Memory* : Connaissances vectorisées et indexées par RAG.
5. **Observabilité et Mesure Permanente** : Aucune affirmation de performance sans tests de régression, calcul de latence et évaluation de taux d'hallucination.
