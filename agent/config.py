"""Runtime configuration for the Continuity agent.

Values are read from the process environment. Locally that's populated by
`.env` (via python-dotenv, loaded here); in Cloud Run / Agent Engine those
same variable names are injected from Secret Manager / the deployment
config, so this module needs no branching between environments.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()  # no-op in deployed environments where no .env file exists


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "See .env.example at the repo root."
        )
    return value


def _list_env(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    # GCP / Vertex AI
    gcp_project: str = field(default_factory=lambda: _require("GOOGLE_CLOUD_PROJECT"))
    gcp_location: str = field(default_factory=lambda: os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    use_vertexai: bool = field(
        default_factory=lambda: os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "True").lower() == "true"
    )
    gemini_model: str = field(default_factory=lambda: os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"))
    staging_bucket: str = field(default_factory=lambda: os.environ.get("AGENT_ENGINE_STAGING_BUCKET", ""))

    # Grafana
    grafana_url: str = field(default_factory=lambda: os.environ.get("GRAFANA_URL", ""))
    grafana_api_key: str = field(default_factory=lambda: os.environ.get("GRAFANA_API_KEY", ""))
    grafana_prometheus_ds_uid: str = field(
        default_factory=lambda: os.environ.get("GRAFANA_PROMETHEUS_DATASOURCE_UID", "")
    )
    grafana_loki_ds_uid: str = field(default_factory=lambda: os.environ.get("GRAFANA_LOKI_DATASOURCE_UID", ""))

    # Postgres
    database_url: str = field(default_factory=lambda: os.environ.get("DATABASE_URL", ""))

    # Remediation guardrails
    remediation_allowlist: list[str] = field(
        default_factory=lambda: _list_env(
            "REMEDIATION_ACTION_ALLOWLIST", "restart_node,rollback_deploy,file_incident_report"
        )
    )
    max_autonomous_remediations_per_hour: int = field(
        default_factory=lambda: int(os.environ.get("MAX_AUTONOMOUS_REMEDIATIONS_PER_HOUR", "3"))
    )


_settings: Settings | None = None


def get_settings() -> Settings:
    """Lazily build and cache Settings so importing this module never fails
    just because env vars aren't set yet (e.g. during local dev, tests, or
    `adk web`'s auto-discovery)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
