# DGAI — Registre des Modèles (Model Registry)

## 1. Gouvernance et Métadonnées

Le `ModelRegistry` (`dgai.llm.registry.ModelRegistry`) centralise le catalogue des modèles supportés par DGAI.

Chaque entrée stocke des métadonnées vérifiables :
- `model_id` : Identifiant unique normalisé.
- `name` & `family` : Nom usuel et famille d'architecture (Mistral, Qwen, Llama, etc.).
- `version` : Version sémantique.
- `engine` : Moteur d'inférence requis (`ExecutionEngine.MOCK`, `LLAMA_CPP`, `TRANSFORMERS`, `VLLM`).
- `capabilities` : Liste de capacités attestées (`TEXT_GENERATION`, `CHAT`, `CODE`, `REASONING`, `MULTILINGUAL`).
- `supported_languages` : Langues prises en charge (codes ISO).
- `context_window_tokens` : Fenêtre de contexte maximale.
- `required_ram_mb` & `required_vram_mb` : Empreinte mémoire mesurée.
- `is_mock` : Booléen signalant les simulateurs de banc de test.
- `license` : Licence d'utilisation des poids (Apache-2.0, MIT, Llama Community, etc.).
- `status` : Statut opérationnel (`AVAILABLE`, `LOADING`, `LOADED`, `UNLOADED`, `ERROR`).

---

## 2. Opérations Supportées

- `register_model(metadata)` : Ajout ou mise à jour d'un modèle.
- `unregister_model(model_id)` : Retrait d'un modèle.
- `get_model(model_id)` : Consultation par identifiant (lève `ModelNotFoundError` si absent).
- `list_models()` : Énumération de l'ensemble des modèles.
- `find_by_capability(capability)` : Recherche par capacité requise.
- `find_by_engine(engine)` : Filtrage par runtime d'exécution.
- `set_status(model_id, status)` : Mise à jour de l'état opérationnel.
