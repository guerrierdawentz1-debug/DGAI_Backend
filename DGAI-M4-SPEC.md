# DGAI — SPÉCIFICATION MAÎTRESSE DU POST-ENTRAÎNEMENT ASSISTANT

**Identifiant :** DGAI-M4-SPEC
**Version :** 6.0.0
**Statut :** Spécification de référence pour l'ingénierie, l'entraînement, l'évaluation, la sécurité et le déploiement
**Module :** M4 — Post-entraînement « Assistant »

---

## Architecture des Modules

- **`dgai/constitution.py`** : Hiérarchie normative à 11 articles (Sécurité > Éthique > Consignes > Utilité).
- **`dgai/m4a_format.py`** : Validation du format conversationnel JSON, packing et masque de perte.
- **`dgai/m4b_sft.py` & `dgai/m4b_data_generator.py`** : Génération procédurale du corpus SFT jusqu'à 1 000 000 d'exemples, déduplication et décontamination.
- **`dgai/m4c_constitutional.py`** : Boucle de révision constitutionnelle en 7 étapes.
- **`dgai/m4d_preference.py`** : Détection du reward hacking (flatterie, verbosité, sycophantie).
- **`dgai/m4e_rewards.py`** : Récompenses vérifiables pour calculs mathématiques, schémas JSON/XML et exécution de code Python sandboxé.
- **`dgai/m4f_calibration.py`** : Calcul de l'ECE (Expected Calibration Error) et benchmark de non-flagornerie.
- **`dgai/search_engine.py`** : Recherche Web grounded en direct avec les API Wikipédia et DuckDuckGo.
- **`dgai/tools.py`** : Calculatrice mathématique sécurisée par AST, horloge UTC, informations système et mémoire de session.
- **`dgai/reasoning.py`** : Moteur de raisonnement avec traces `<thought>` et pipeline Q&A.
- **`dgai/response_style.py`** : Contrôleur de style de réponse (`short`, `detailed`, `bullet_points`, `structured`).
