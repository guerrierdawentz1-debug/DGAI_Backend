# DGAI Backend & AI Assistant Framework

Spécification maîtresse post-entraînement **DGAI-M4-SPEC v6.0.0**.

## Endpoints principaux

- `POST /predict` & `POST /api/v1/predict` : Endpoint compatible texte/Q&A et prédictions numériques scikit-learn MLPRegressor.
- `POST /api/v1/chat` : Pipeline de conversation Q&A complet avec traces de raisonnement `<thought>`.
- `POST /api/v1/ask` : Question/Réponse directe.
- `GET /api/v1/tools` & `POST /api/v1/tools/execute` : API d'outillage DGAI.
- `POST /api/v1/m4b/sft/generate_corpus` : Génération à la demande de corpus jusqu'à 1 000 000 d'exemples.

## Exécution des tests

```bash
python3 -m pytest
```
