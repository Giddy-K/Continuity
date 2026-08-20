"""Tool: query_alerts - pull currently firing/pending alerts from Grafana."""

from __future__ import annotations

from typing import Any

from grafana_client import GrafanaClient


def query_alerts() -> dict[str, Any]:
    """Fetch the current set of firing or pending Grafana alert instances.

    This is the agent's detection entry point: it's called first, on a
    schedule or in response to a webhook, to see whether anything in the
    render pipeline / CDN / license-check dashboards is currently unhealthy.

    Returns:
        A dict with:
          - "alerts": list of alert instances, each containing at least
            "labels" (alertname, severity, service), "status", and
            "activeAt".
          - "count": number of alerts returned.
    """
    client = GrafanaClient()
    alerts = client.list_alert_instances()
    return {"alerts": alerts, "count": len(alerts)}
