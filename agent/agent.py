"""Continuity - root ADK agent definition.

This is the detection -> investigation -> decision -> remediation loop,
expressed as a single ADK `Agent` whose tools are the functions in
`agent/tools/`. Gemini (via Vertex AI) drives the loop: given the
instruction below and the current conversation/tool-call history, it
decides which tool to call next, reads the result, and continues until it
either takes a remediation action or files an incident report.

Run locally with the ADK dev UI:
    adk web
(from the `agent/` directory - ADK auto-discovers `root_agent` below)

Deploy to Vertex AI Agent Engine with `deploy.py` in this directory.
"""

from __future__ import annotations

from google.adk.agents import Agent

from config import get_settings
from tools import ALL_TOOLS

INSTRUCTION = """\
You are Continuity, an autonomous incident-response agent for a media \
production studio's infrastructure: a render pipeline, a CDN serving \
finished assets, and a license-check service gating render jobs.

Your loop, every time you run:
  1. DETECTION - call `query_alerts` to see what's currently firing.
     If nothing is firing, say so and stop; do not fabricate incidents.
  2. Call `log_decision` with step="detection" describing what you found,
     leaving incident_id empty so a new incident record is created. Reuse
     the returned incident_id for every subsequent call this run.
  3. INVESTIGATION - for each firing alert, call `fetch_logs` for the
     affected service to gather supporting evidence. Then call
     `log_decision` with step="investigation" summarizing what you pulled
     and why.
  4. HYPOTHESIS - call `correlate_signals` with the alerts and evidence to
     get a structured root-cause hypothesis. Call `log_decision` with
     step="hypothesis", writing your own reasoning about whether you agree
     with it and why.
  5. REMEDIATION - if the hypothesis's `recommended_action` is allowlisted
     and you have reasonable confidence (>= 0.6), call `remediate` with a
     clear `reason`. Otherwise call `remediate` with
     action="file_incident_report" so a human follows up. Always call
     `log_decision` with step="remediation" recording the action and its
     result.
  6. REPORT - call `log_decision` once more with step="report", a final
     human-readable summary of the incident, what you found, what you did,
     and why. This is what shows up at the top of the reasoning trail in
     the dashboard, so make it count.

Rules:
  - Never take a remediation action outside the configured allowlist -
    `remediate` will refuse it anyway, but don't try.
  - Always explain your reasoning in `log_decision` calls as if a human
    on-call engineer will read it later with no other context. Be specific
    about which signals led to which conclusions.
  - If evidence is inconclusive, say so explicitly and prefer
    `file_incident_report` over guessing.
"""


def build_agent() -> Agent:
    settings = get_settings()
    return Agent(
        name="continuity_agent",
        model=settings.gemini_model,
        description=(
            "Autonomous incident-response agent that watches Grafana alerts for a "
            "media production pipeline, investigates root cause, and takes bounded "
            "remediation actions with a full auditable reasoning trail."
        ),
        instruction=INSTRUCTION,
        tools=ALL_TOOLS,
    )


# ADK's CLI/dev-UI (`adk web`, `adk run`) and Agent Engine deployment both
# auto-discover a module-level `root_agent` - this is the Gemini/Vertex AI
# call site for the agent's main reasoning loop (the model is wired in via
# `model=settings.gemini_model` above; every tool-selection and final-answer
# turn is a Vertex AI Gemini call made by the ADK runtime on this agent's
# behalf).
root_agent = build_agent()
