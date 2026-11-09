# DGAI Backend — Post-Entraînement Assistant (DGAI-M4-SPEC v6.0.0)

DGAI est un système d'assistant IA autonome et modulaire, conçu conformément à la spécification **DGAI-M4-SPEC (v6.0.0)**. Il met en oeuvre un post-entraînement complet comprenant la gestion du format conversationnel, l'alignement constitutionnel, la vérification des récompenses et l'évaluation de la calibration et de la non-flagornerie.

---

## Structure du projet

```
.
├── DGAI-M4-SPEC.md           # Spécification maîtresse DGAI-M4-SPEC v6.0.0
├── README.md                 # Documentation du projet
├── Dockerfile                # Environnement Docker Python 3.11-slim
├── requirements.txt          # Dépendances Python
├── main.py                   # Serveur Flask DGAI API (endpoints ML & M4)
├── dgai/                     # Core DGAI Post-Training Framework
│   ├── __init__.py
│   ├── constitution.py       # Constitution & hiérarchie normative
│   ├── m4a_format.py         # Format conversationnel & masquage de perte
│   ├── m4b_sft.py            # SFT data pipeline, dédoublonnage & décontamination
│   ├── m4c_constitutional.py # Boucle de révision Constitutional AI
│   ├── m4d_preference.py     # Préférences, RLAIF & détection du reward hacking
│   ├── m4e_rewards.py        # Moteur de récompenses vérifiables (Math, Code, Schémas)
│   └── m4f_calibration.py    # Calibration ECE, honnêteté & tests de non-flagornerie
└── tests/                    # Suite de tests automatisés (pytest)
    ├── test_dgai_modules.py  # Tests unitaires des modules core
    └── test_api.py           # Tests d'intégration API Flask
```

---

## Fonctionnalités Principales

1. **Hiérarchie Normative & Constitution (`dgai/constitution.py`)** :
   - Application stricte : **Sécurité > Éthique > Consignes de l'opérateur > Utilité**.
2. **Format Conversationnel M4a (`dgai/m4a_format.py`)** :
   - Validation des rôles (`system`, `developer`, `user`, `assistant`, `tool`), extraction d'appels d'outils et calcul des masques de perte de tokens.
3. **Pipeline SFT M4b (`dgai/m4b_sft.py`)** :
   - Traçabilité des métadonnées, dédoublonnage exact/approximatif et décontamination automatique vis-à-vis des jeux de test.
4. **Constitutional AI M4c (`dgai/m4c_constitutional.py`)** :
   - Génération candidate, évaluation constitutionnelle, critique et révision vérifiée.
5. **Préférences & RLAIF M4d (`dgai/m4d_preference.py`)** :
   - Évaluation de paires de préférences et détection des comportements de *reward hacking* (ex. verbosité excessive, flatterie/sycophannie).
6. **Récompenses Vérifiables M4e (`dgai/m4e_rewards.py`)** :
   - Évaluation déterministe en Mathématiques (tolérances), Programmation (tests unitaires) et Formats (JSON/XML).
7. **Calibration & Non-Flagornerie M4f (`dgai/m4f_calibration.py`)** :
   - Calcul de l'**ECE (Expected Calibration Error)**, exactitude factuelle, abstention calibrée et résistance à la pression sociale.

---

## Directives d'utilisation API

| Endpoint | Méthode | Description |
|---|---|---|
| `/` | `GET` | Statut du serveur et version DGAI-M4-SPEC |
| `/api/v1/init` | `POST` | Initialisation du modèle MLPRegressor backend |
| `/api/v1/train` | `POST` | Entraînement du modèle backend |
| `/api/v1/predict` | `POST` | Prédiction par le modèle backend |
| `/api/v1/m4a/format` | `POST` | Validation du format conversationnel & masques de perte |
| `/api/v1/m4b/sft/decontaminate` | `POST` | Dédoublonnage & décontamination du dataset SFT |
| `/api/v1/m4c/constitutional/review` | `POST` | Exécution de la boucle de révision constitutionnelle |
| `/api/v1/m4d/preferences/evaluate` | `POST` | Évaluation des préférences et détection du reward hacking |
| `/api/v1/m4e/rewards/verify` | `POST` | Calcul de la récompense vérifiable (math, code, schéma) |
| `/api/v1/m4f/metrics/ece` | `POST` | Calcul de l'ECE et métriques d'incertitude/honnêteté |
| `/api/v1/m4f/sycophancy/evaluate` | `POST` | Évaluation de la stabilité sous pression de l'utilisateur |

---

## Tests & Lancement

Lancer le serveur Flask :
```bash
python main.py
```

Exécuter la suite de tests :
```bash
python -m pytest
```
