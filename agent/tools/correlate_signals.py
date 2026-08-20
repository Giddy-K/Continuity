"""Tool: correlate_signals - synthesize alerts/logs/metrics into a root-cause
hypothesis using a direct Gemini call via the `google-genai` SDK.

Most of the agent's reasoning happens implicitly, through Gemini's native
function-calling loop as orchestrated by ADK (see agent.py). This tool is
the one place the agent makes an *explicit*, second Gemini call mid-flow -
useful when we want a structured, single-purpose synthesis (a root-cause
hypothesis + confidence score) rather than another free-form agent turn.
"""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types

from config import get_settings

_CORRELATION_PROMPT = """\
You are an SRE assistant correlating observability signals for a media \
production pipeline (render workers, CDN edge, license-check service).

Given the alert(s) that fired and the logs/metrics gathered during \
investigation, produce a single root-cause hypothesis.

Alerts:
{alerts}

Logs/metrics evidence:
{evidence}

Respond as JSON with exactly these keys:
  "hypothesis": one paragraph, plain-English root cause explanation
  "confidence": float between 0 and 1
  "recommended_action": one of "restart_node", "rollback_deploy", \
"file_incident_report", or "none"
  "evidence_summary": short bullet list (as a single string) of the \
strongest supporting evidence
"""


def correlate_signals(alerts: list[dict[str, Any]], evidence: dict[str, Any]) -> dict[str, Any]:
    """Correlate alerts with investigation evidence to form a root-cause hypothesis.

    This makes an explicit call to Gemini (via `google-genai`, targeting
    Vertex AI) to reason over the structured evidence gathered by
    `query_alerts` and `fetch_logs`, and returns a structured hypothesis the
    agent can act on with `remediate`.

    Args:
        alerts: The alert list returned by `query_alerts`.
        evidence: The logs/metrics dict returned by `fetch_logs`.

    Returns:
        A dict with "hypothesis", "confidence", "recommended_action", and
        "evidence_summary".
    """
    settings = get_settings()

    # --- Gemini / Vertex AI call site -----------------------------------
    # This is the explicit runtime call into Vertex AI's Gemini models,
    # separate from the ADK agent's own model turns.
    client = genai.Client(
        vertexai=settings.use_vertexai,
        project=settings.gcp_project,
        location=settings.gcp_location,
    )
    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=_CORRELATION_PROMPT.format(
            alerts=json.dumps(alerts, indent=2, default=str),
            evidence=json.dumps(evidence, indent=2, default=str),
        ),
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )
    # ----------------------------------------------------------------------

    try:
        return json.loads(response.text)
    except (json.JSONDecodeError, TypeError):
        return {
            "hypothesis": response.text or "Model returned no parseable content.",
            "confidence": 0.0,
            "recommended_action": "none",
            "evidence_summary": "",
        }
