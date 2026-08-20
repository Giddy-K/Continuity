"""Thin client around the Grafana HTTP API.

This is the one place that talks to Grafana Cloud directly. Tools in
`agent/tools/` call into this module rather than hitting `httpx` themselves,
so auth, base URL, and error handling stay in one spot.

Docs: https://grafana.com/docs/grafana/latest/developers/http_api/
"""

from __future__ import annotations

from typing import Any

import httpx

from config import get_settings


class GrafanaClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.grafana_url).rstrip("/")
        self._api_key = api_key or settings.grafana_api_key

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Alerting
    # ------------------------------------------------------------------
    def list_alert_instances(self) -> list[dict[str, Any]]:
        """GET /api/alertmanager/grafana/api/v2/alerts - currently firing/pending alerts."""
        with httpx.Client(base_url=self._base_url, headers=self._headers(), timeout=15) as client:
            resp = client.get("/api/alertmanager/grafana/api/v2/alerts")
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Metrics (Prometheus datasource, proxied through Grafana)
    # ------------------------------------------------------------------
    def query_prometheus(self, datasource_uid: str, promql: str, time_range_seconds: int = 900) -> dict[str, Any]:
        """POST /api/ds/query - instant/range PromQL query via Grafana's datasource proxy."""
        payload = {
            "queries": [
                {
                    "refId": "A",
                    "datasource": {"uid": datasource_uid, "type": "prometheus"},
                    "expr": promql,
                    "range": True,
                    "intervalMs": 15000,
                    "maxDataPoints": 500,
                }
            ],
            "from": f"now-{time_range_seconds}s",
            "to": "now",
        }
        with httpx.Client(base_url=self._base_url, headers=self._headers(), timeout=30) as client:
            resp = client.post("/api/ds/query", json=payload)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Logs (Loki datasource, proxied through Grafana)
    # ------------------------------------------------------------------
    def query_loki(self, datasource_uid: str, logql: str, time_range_seconds: int = 900, limit: int = 200) -> dict[str, Any]:
        """POST /api/ds/query - LogQL query via Grafana's datasource proxy."""
        payload = {
            "queries": [
                {
                    "refId": "A",
                    "datasource": {"uid": datasource_uid, "type": "loki"},
                    "expr": logql,
                    "maxLines": limit,
                }
            ],
            "from": f"now-{time_range_seconds}s",
            "to": "now",
        }
        with httpx.Client(base_url=self._base_url, headers=self._headers(), timeout=30) as client:
            resp = client.post("/api/ds/query", json=payload)
            resp.raise_for_status()
            return resp.json()

    # ------------------------------------------------------------------
    # Annotations (used to mark remediation actions on Grafana dashboards)
    # ------------------------------------------------------------------
    def create_annotation(self, text: str, tags: list[str] | None = None, dashboard_uid: str | None = None) -> dict[str, Any]:
        """POST /api/annotations - leaves a visible marker on dashboards when the agent acts."""
        payload: dict[str, Any] = {"text": text, "tags": tags or ["continuity-agent"]}
        if dashboard_uid:
            payload["dashboardUID"] = dashboard_uid
        with httpx.Client(base_url=self._base_url, headers=self._headers(), timeout=15) as client:
            resp = client.post("/api/annotations", json=payload)
            resp.raise_for_status()
            return resp.json()
