"""Tool: log_decision - write one auditable step to the Postgres incident log.

This is the tool that makes the agent's reasoning inspectable after the
fact. The agent is instructed (see agent.py) to call this after every
meaningful step - detection, investigation, hypothesis, remediation, and
final report - so the Next.js dashboard can render a full trail, not just
the end result.
"""

from __future__ import annotations

from typing import Any

import db


def log_decision(
    step: str,
    reasoning: str,
    incident_id: str = "",
    incident_title: str = "",
    severity: str = "medium",
    source_alert: str = "",
    action_taken: str = "",
    action_result: str = "",
) -> dict[str, Any]:
    """Record one step of the agent's reasoning trail to the audit log.

    If `incident_id` is empty, a new incident is created (this should only
    happen on the "detection" step) and its id is returned so subsequent
    calls in the same investigation can reference it.

    Args:
        step: One of "detection", "investigation", "hypothesis",
            "remediation", "report".
        reasoning: The agent's own explanation of why it took this step /
            reached this conclusion. Written verbatim to the audit trail.
        incident_id: The incident this decision belongs to. Leave empty
            only for the very first ("detection") call.
        incident_title: Required when creating a new incident (incident_id
            empty). Short human-readable summary, e.g. "CDN 5xx spike -
            eu-west edge".
        severity: One of "low", "medium", "high", "critical". Only used
            when creating a new incident.
        source_alert: The Grafana alert name/UID that triggered detection.
            Only used when creating a new incident.
        action_taken: Name of the remediation action taken this step, if
            any (mirrors `remediate`'s `action` argument).
        action_result: Outcome/status of the action taken this step, if any.

    Returns:
        A dict with "incident_id" and "decision_id".
    """
    if not incident_id:
        incident_id = db.create_incident(
            title=incident_title or "Untitled incident",
            severity=severity,
            source_alert=source_alert or None,
        )

    decision_id = db.record_decision(
        incident_id=incident_id,
        step=step,
        reasoning=reasoning,
        action_taken=action_taken or None,
        action_result=action_result or None,
    )

    return {"incident_id": incident_id, "decision_id": decision_id}
