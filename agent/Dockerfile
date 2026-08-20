# Continuity agent - Cloud Run image.
#
# Cloud Run here hosts a thin FastAPI/ADK wrapper for local testing and
# webhook-triggered runs; the primary deployment target for the agent
# itself is Vertex AI Agent Engine (see deploy.py). Secrets (Grafana token,
# DB credentials) are injected as env vars from Secret Manager at deploy
# time - never baked into this image.

FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
