# Setup

## Prerequisites

- Python 3.11+
- Node.js 20+
- Postgres 15+ (local or Cloud SQL)
- A Grafana Cloud stack (free tier is fine) with Prometheus + Loki
- A GCP project with Vertex AI enabled, and `gcloud` authenticated
  (`gcloud auth application-default login`)

## 1. Clone and configure environment variables

```bash
cp .env.example .env
```

Fill in:
- `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `AGENT_ENGINE_STAGING_BUCKET`,
  `GCP_SERVICE_ACCOUNT_EMAIL` - from your GCP project (ask the project
  owner; these must match a real project, don't invent values).
- `GRAFANA_URL`, `GRAFANA_API_KEY`, `GRAFANA_PROMETHEUS_DATASOURCE_UID`,
  `GRAFANA_LOKI_DATASOURCE_UID` - from your Grafana Cloud stack (see
  `/grafana/README.md`).
- `DATABASE_URL` - your local or Cloud SQL Postgres instance.

`.env` is git-ignored. In deployed environments these are injected from
Secret Manager instead - see `docs/setup.md#secrets` below.

## 2. Database

```bash
createdb continuity
psql continuity -f db/schema.sql
```

## 3. Grafana

Follow `/grafana/README.md` to import the dashboards and alert rules, and
point a Prometheus + Promtail pair (or your own metric/log emitters) at
your Grafana Cloud stack.

## 4. Agent

```bash
cd agent
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Local dev UI with full tool-call tracing:
adk web

# Or run the Cloud Run-style webhook server locally:
uvicorn server:app --reload --port 8080
```

## 5. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # set DATABASE_URL_READONLY
npm run dev
```

Visit http://localhost:3000.

## 6. Deploying

- **Agent → Vertex AI Agent Engine**: `python agent/deploy.py` (requires
  `GOOGLE_CLOUD_PROJECT` / `GOOGLE_CLOUD_LOCATION` /
  `AGENT_ENGINE_STAGING_BUCKET` set to real values).
- **Agent → Cloud Run** (webhook-triggered variant): build/deploy
  `agent/Dockerfile`, injecting all secrets from Secret Manager rather than
  a `.env` file:
  ```bash
  gcloud run deploy continuity-agent \
    --source agent \
    --region "$GOOGLE_CLOUD_LOCATION" \
    --set-secrets GRAFANA_API_KEY=grafana-api-key:latest,DATABASE_URL=continuity-db-url:latest \
    --service-account "$GCP_SERVICE_ACCOUNT_EMAIL"
  ```
- **Frontend → Vercel or Cloud Run**: standard Next.js deploy; set
  `DATABASE_URL_READONLY` as a platform secret.

### Secrets

Never commit `.env`. Locally it's a plain file (git-ignored); in GCP,
every value in `.env.example` should have a corresponding Secret Manager
secret, referenced via `--set-secrets` (Cloud Run) or the Agent Engine
deployment config, not hardcoded.

## GCP-specific values that need to match a real project

The following are placeholders in `.env.example` and must be supplied by
whoever owns the target GCP project before deploying - do not guess them:
`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`,
`AGENT_ENGINE_STAGING_BUCKET`, `GCP_SERVICE_ACCOUNT_EMAIL`.
