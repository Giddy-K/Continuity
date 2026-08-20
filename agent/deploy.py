"""Deploy the Continuity agent to Vertex AI Agent Engine.

This wraps `root_agent` in ADK's `AdkApp` and calls
`vertexai.agent_engines.create`, which is the actual Vertex AI Agent Engine
call site for this project (as opposed to `server.py`, which is the Cloud
Run path). See:
https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/agent-engine/intro_agent_engine.ipynb

Usage:
    python deploy.py

Requires GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION, and
AGENT_ENGINE_STAGING_BUCKET to be set (see .env.example) and match a real
GCP project you have deploy access to.
"""

from __future__ import annotations

import vertexai
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

from agent import root_agent
from config import get_settings


def main() -> None:
    settings = get_settings()

    # --- Vertex AI init / Agent Engine call site -------------------------
    vertexai.init(
        project=settings.gcp_project,
        location=settings.gcp_location,
        staging_bucket=settings.staging_bucket,
    )

    app = AdkApp(agent=root_agent, enable_tracing=True)

    remote_agent = agent_engines.create(
        app,
        requirements=[
            "google-cloud-aiplatform[agent_engines,adk]>=1.101.0",
            "google-genai>=1.20.0",
            "httpx>=0.27.0",
            "psycopg[binary]>=3.2.0",
        ],
        display_name="continuity-agent",
        description="Autonomous incident-response agent for a media production pipeline.",
    )
    # ----------------------------------------------------------------------

    print(f"Deployed. Resource name: {remote_agent.resource_name}")


if __name__ == "__main__":
    main()
