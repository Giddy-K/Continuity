"""Tool: fetch_logs - pull metrics and logs for a service from Grafana."""

from __future__ import annotations

from typing import Any

from config import get_settings
from grafana_client import GrafanaClient


def fetch_logs(
    service: str,
    logql_filter: str = "",
    promql_query: str = "",
    lookback_seconds: int = 900,
) -> dict[str, Any]:
    """Pull recent logs (Loki) and/or metrics (Prometheus) for a service.

    Called during investigation, after `query_alerts` identifies a firing
    alert, to gather the evidence needed to form a root-cause hypothesis.

    Args:
        service: Name of the affected service, e.g. "render-worker-03",
            "cdn-edge", "license-check-svc". Used to scope the default
            LogQL/PromQL selectors when explicit queries aren't given.
        logql_filter: Optional explicit LogQL query. If empty, defaults to
            `{service="<service>"} |= ""` (all recent log lines for the
            service).
        promql_query: Optional explicit PromQL query. If empty, no metrics
            are fetched.
        lookback_seconds: How far back to look, in seconds. Defaults to the
            last 15 minutes.

    Returns:
        A dict with "logs" (raw Loki query response) and "metrics" (raw
        Prometheus query response, or None if promql_query was empty).
    """
    settings = get_settings()
    client = GrafanaClient()

    logql = logql_filter or f'{{service="{service}"}} |= ""'
    logs = client.query_loki(
        datasource_uid=settings.grafana_loki_ds_uid,
        logql=logql,
        time_range_seconds=lookback_seconds,
    )

    metrics = None
    if promql_query:
        metrics = client.query_prometheus(
            datasource_uid=settings.grafana_prometheus_ds_uid,
            promql=promql_query,
            time_range_seconds=lookback_seconds,
        )

    return {"service": service, "logs": logs, "metrics": metrics}
