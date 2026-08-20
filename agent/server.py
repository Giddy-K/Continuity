"""Minimal Cloud Run wrapper around the ADK agent.

Exposes:
  GET  /health         - liveness check
  POST /webhook/alert   - Grafana webhook receiver; triggers one run of the
                           detection -> investigation -> decision ->
                           remediation loop via `root_agent`.

For local iteration, prefer `adk web` (from this directory) over this
server - it gives you the ADK dev UI with full tool-call tracing. This
server exists so the agent can also be driven by a real Grafana alert
webhook when deployed to Cloud Run.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from google.adk.runners import InMemoryRunner
from google.genai import types

from agent import root_agent

app = FastAPI(title="Continuity Agent")

# ADK Runner drives the agent's tool-calling loop; this is the same Gemini
# (via Vertex AI) call path used by `adk web` / `adk run`, just invoked
# programmatically here instead of through the CLI.
_runner = InMemoryRunner(agent=root_agent, app_name="continuity")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook/alert")
async def handle_alert_webhook(request: Request) -> dict[str, str]:
    payload = await request.json()

    session = await _runner.session_service.create_session(
        app_name="continuity", user_id="grafana-webhook"
    )
    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    "A Grafana alert webhook just fired with this payload. "
                    "Run your detection -> investigation -> decision -> "
                    f"remediation loop.\n\n{payload}"
                )
            )
        ],
    )

    events = []
    async for event in _runner.run_async(
        user_id="grafana-webhook", session_id=session.id, new_message=message
    ):
        events.append(event)

    return {"status": "completed", "session_id": session.id, "event_count": str(len(events))}
