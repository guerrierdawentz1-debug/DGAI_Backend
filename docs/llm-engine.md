# DGAI — Moteur Central LLM & Inférence

## 1. Principes Directeurs et Indépendance

DGAI n'est pas un proxy vers un modèle propriétaire externe. Le moteur LLM (`dgai.llm.engine.LLMEngine`) est conçu comme un runtime d'exécution modulaire et asynchrone capable d'accueillir des modèles de langage ouverts (open-weight) exécutés localement.

### Règles d'Intégrité
1. **Transparence Absolue** : Aucun modèle n'est déclaré "entraîné par DGAI" tant qu'un pipeline d'entraînement formel n'a pas été exécuté avec métriques vérifiables.
2. **Fournisseur Mock** : Le `MockModelProvider` est strictement réservé aux tests unitaires et d'intégration automatisés. Il est formellement interdit en environnement de production (`EnvironmentType.PRODUCTION`). Ses réponses portent le préfixe explicite `[MOCK_TEST_RESPONSE]` et `is_mock: true`.
3. **Absence de Modèle** : Lorsque aucun modèle réel n'est initialisé en mémoire, l'API répond avec une erreur explicite `HTTP 503 Service Unavailable`, informant honnêtement que le moteur IA n'est pas encore disponible.

---

## 2. Architecture des Composants

```
[Requête Utilisateur (API)]
            │
            ▼
[IntentAnalyzer & BrainRouter] ──> Détermine l'intention, capacités requises et modèle cible
            │
            ▼
      [LLMEngine] ───────────────> Contrôle de concurrence (Semaphore) & Timeouts
            │
    ┌───────┴───────────────────┐
    ▼                           ▼
[ModelRegistry]        [BaseModelProvider]
(Métadonnées,          ├── MockModelProvider (Tests)
 Licences, VRAM)       ├── LlamaCppProvider (Prévu Phase future)
                       └── TransformersProvider (Prévu Phase future)
```

---

## 3. Interfaces Techniques

- **`BaseModelProvider`** (`dgai/llm/providers/base.py`) :
  - `load_model(metadata)` : Chargement en mémoire des poids.
  - `unload_model(model_id)` : Libération des ressources VRAM/RAM.
  - `is_ready(model_id)` : Vérification de la disponibilité du modèle.
  - `generate(request, metadata)` : Inférence asynchrone bornée par timeout.
- **`LLMEngine`** (`dgai/llm/engine.py`) :
  - Normalisation des requêtes.
  - Plafonnement des tokens (`max_generation_tokens`).
  - Validation de longueur des prompts (`max_prompt_length_chars`).
  - Gestion des requêtes simultanées (`llm_max_concurrent_requests`).
