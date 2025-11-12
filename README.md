# shopyverse-reco-service

Micro-service de recommandation de produits (FastAPI) — propulsé par un LLM via LangChain + Hugging Face.

Fonctionnalités principales

- HTTP API (FastAPI) pour ingérer des produits et obtenir des recommandations
- Recommender service : pré-filtrage par catégorie / gamme de prix, puis reranking par un LLM (Llama-3.1-8B-Instruct)
- Intégration LangChain -> Hugging Face (via `langchain_huggingface` / `HuggingFaceEndpoint` + `ChatHuggingFace`)

Prérequis

- Python 3.11+
- Un token Hugging Face valide accessible via la variable d'environnement `HUGGINGFACEHUB_API_TOKEN`

Installation (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Variables d'environnement importantes

- `HUGGINGFACEHUB_API_TOKEN` : ton token Hugging Face (utilisé par `huggingface_hub`)
- `DATABASE_URL` : URL Postgres (déjà utilisé par l'app)

Exécution locale

```bash
# (dans l'environnement virtuel)
uvicorn src.main:app --reload
```

Endpoints principaux

- POST /api/products  -- ingérer un produit (body: id, name, description, category, price...)
- GET /api/recommendations?product_id=<uuid>&k=5  -- obtenir recommandations pour un produit

Comportement du recommender

- Récupère le produit cible en base
- Pré-filtre des candidats (même `category` et prix dans +/-20%)
- Construit un prompt listant le produit cible et les candidats
- Envoie le prompt au LLM via LangChain/HuggingFace
- Parse la réponse JSON et renvoie la liste des `product_id` existants en base (filtre les hallucinations)

Docker

Le projet inclut un `Dockerfile` et `docker-compose.yml` pour exécuter le service + Postgres.

Exemples de commandes Docker

```bash
# build image avec docker compose
docker compose build

# run (en injectant les variables d'environnement)
docker compose up --build

# détaché
docker compose up -d --build

# voir logs
docker compose logs -f

# arrêter
docker compose down
```

Tests et développement

- Ajoute des produits via `POST /api/products` (ou la route d'ingestion que tu as déjà) pour peupler la base.
- Appelle `GET /api/recommendations?product_id=<uuid>&k=5` pour tester le flux. Les logs montrent l'appel LLM et la parsing JSON. Si le LLM produit des IDs absents de la DB, le service les filtrera automatiquement.

# reco service
