"""Tool: remediate - take a bounded, allowlisted remediation action.

Every action here is deliberately narrow and reversible-by-design. The
agent can only take actions in `settings.remediation_allowlist`; anything
else is refused and downgraded to filing an incident report for a human.
"""

from __future__ import annotations

from typing import Any

from config import get_settings
from grafana_client import GrafanaClient


def remediate(action: str, target: str, reason: str) -> dict[str, Any]:
    """Execute a bounded remediation action, or file a report if none applies.

    Supported actions (see REMEDIATION_ACTION_ALLOWLIST in .env):
      - "restart_node": restart a specific failing render/CDN node.
      - "rollback_deploy": roll the named service back to its previous
        known-good deploy.
      - "file_incident_report": no infrastructure change; records a
        structured report for human follow-up. Always available as a
        fallback.

    Args:
        action: One of the supported action names above.
        target: The node/service/deploy identifier the action applies to.
        reason: The reasoning that justifies this action - stored in the
            audit trail alongside the result.

    Returns:
        A dict with "action", "target", "status" ("executed", "refused", or
        "reported"), and "detail".
    """
    settings = get_settings()

    if action not in settings.remediation_allowlist:
        return {
            "action": action,
            "target": target,
            "status": "refused",
            "detail": f"'{action}' is not in the remediation allowlist: {settings.remediation_allowlist}",
        }

    client = GrafanaClient()

    if action == "file_incident_report":
        detail = f"Incident report filed for {target}: {reason}"
    elif action == "restart_node":
        # TODO: wire up to the actual infra control plane (e.g. a Cloud Run
        # job, GKE API call, or render-farm orchestrator endpoint). Left as
        # a stub for the demo environment.
        detail = f"Restart requested for node '{target}' (stub - no real infra call wired up yet)."
    elif action == "rollback_deploy":
        # TODO: wire up to the actual deploy system (e.g. Cloud Deploy API).
        detail = f"Rollback requested for '{target}' (stub - no real infra call wired up yet)."
    else:
        detail = f"Unhandled allowlisted action '{action}'."

    # Leave a visible marker on the relevant Grafana dashboard so the action
    # shows up alongside the metrics it was meant to fix.
    client.create_annotation(
        text=f"Continuity agent: {action} on {target} - {reason}",
        tags=["continuity-agent", action],
    )

    return {"action": action, "target": target, "status": "executed", "detail": detail}
