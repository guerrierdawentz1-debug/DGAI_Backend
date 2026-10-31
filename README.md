# DGAI — Assistant IA Autonome et Modulaire

DGAI est un projet d'intelligence artificielle indépendant, conçu autour d'une architecture modulaire, sécurisée et extensible, exploitant des modèles de langage ouverts sans dépendre obligatoirement d'API propriétaires externes.

---

## Architecture Générale (Cerveau DGAI)

Le système sépare strictement les responsabilités :
- **DGAI Core (`dgai.core`)** : Configuration immuable validée (Pydantic Settings), journalisation structurée JSON, cycle de vie.
- **LLM Engine (`dgai.llm`)** : Interface d'inférence locale indépendante du runtime, support des modèles open-weight et gestion des licences.
- **Raisonnement & Routage (`dgai.reasoning`)** : Classification d'intention, planification structurée (Chain-of-Thought, ReAct) et gestion du budget de contexte.
- **Mémoire & RAG (`dgai.memory`, `dgai.rag`)** : 4 niveaux de mémoire (Short-term, Working, Long-term, Document RAG) et recherche vectorielle.
- **Recherche Web (`dgai.websearch`)** : Multi-fournisseurs, protection anti-SSRF, scraping propre et gestion des citations.
- **Agents Autonomes & Sandbox (`dgai.agents`, `dgai.sandbox`)** : Boucle ReAct sous quotas stricts, isolation de processus non-root.
- **Spécialisations (`dgai.domains`)** : 5 domaines d'expertise (Rédaction, Analyse documentaire, Programmation, Support client, Langues).
- **Sécurité & Observabilité (`dgai.safety`, `dgai.evaluation`)** : Protection contre les injections de prompt, caviardage PII, métriques multi-critères.

---

## 5 Spécialisations Clés

1. **Rédaction et création de contenu**
2. **Analyse et synthèse documentaire**
3. **Programmation et développement logiciel**
4. **Assistance et service client**
5. **Traduction et apprentissage des langues**

---

## Démarrage Rapide

### Prérequis
- Python 3.11 ou supérieur
- Pip

### Installation des dépendances

```bash
git clone <repo_url>
cd dgai
pip install -r requirements.txt
```

### Configuration

Copiez le fichier `.env.example` en `.env` :

```bash
cp .env.example .env
```

Ajustez les variables selon votre environnement (développement, test, production).

### Lancement en mode développement

```bash
./scripts/run_dev.sh
```

### Exécution des tests automatisés

```bash
./scripts/run_tests.sh
# ou directement :
python3 -m pytest -v
```

---

## Déploiement Docker

Le projet intègre un `Dockerfile` sécurisé basé sur un utilisateur non-privilégié (`dgai`):

```bash
docker build -t dgai:latest .
docker run --rm -p 8000:8000 dgai:latest
```

---

## Feuille de Route de Construction

- [x] **Phase 1 : Fondations, Configuration & Journalisation**
- [ ] **Phase 2 : Sécurité & API**
- [ ] **Phase 3 : Moteur LLM Indépendant & Modèles**
- [ ] **Phase 4 : Contexte & Raisonnement**
- [ ] **Phase 5 : Mémoire & RAG**
- [ ] **Phase 6 : Recherche Web Multi-fournisseurs**
- [ ] **Phase 7 : Agents Autonomes & Outils**
- [ ] **Phase 8 : Sandbox Sécurisée**
- [ ] **Phase 9 : Spécialisations Métier**
- [ ] **Phase 10 : Données & Entraînement**
- [ ] **Phase 11 : Multimodalité**
- [ ] **Phase 12 : Évaluation, Optimisation & Déploiement**
