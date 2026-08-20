# Architecture

## Overview

Continuity is a closed-loop incident-response agent: it watches Grafana,
investigates anomalies on a simulated media studio's infrastructure,
forms a root-cause hypothesis with Gemini, takes a bounded remediation
action, and writes every step of its reasoning to an auditable Postgres
log that a Next.js dashboard renders read-only.

```mermaid
flowchart TD
    subgraph Infra["Simulated media studio infra"]
        RP[Render pipeline]
        CDN[CDN edge]
        LC[License-check service]
    end

    RP -- metrics/logs --> Prom[(Prometheus / Mimir)]
    CDN -- metrics/logs --> Prom
    LC -- metrics/logs --> Prom
    RP -- logs --> Loki[(Loki)]
    CDN -- logs --> Loki
    LC -- logs --> Loki

    Prom --> Grafana[Grafana Cloud]
    Loki --> Grafana
    Grafana -- alert rules --> Alerts[Alertmanager]

    subgraph Agent["Continuity agent (ADK, Cloud Run / Agent Engine)"]
        direction TB
        Detect["query_alerts()"] --> Invest["fetch_logs()"]
        Invest --> Correlate["correlate_signals()\n(explicit Gemini call)"]
        Correlate --> Remediate["remediate()\n(bounded, allowlisted)"]
        Detect --> Log["log_decision()"]
        Invest --> Log
        Correlate --> Log
        Remediate --> Log
    end

    Alerts -->|"Grafana API: list alert instances"| Detect
    Grafana -->|"Grafana API: query Prometheus/Loki via /api/ds/query"| Invest
    Remediate -->|"Grafana API: POST /api/annotations"| Grafana

    Gemini["Gemini (Vertex AI)"]
    Correlate <--> Gemini
    Detect -. "tool-calling loop\ndriven by Gemini via ADK" .-> Gemini
    Invest -. "" .-> Gemini
    Remediate -. "" .-> Gemini

    Log --> PG[(Postgres\nincidents + decisions)]
    PG --> FE["Next.js dashboard\n(read-only)"]
```

## Components

- **Simulated infra** - render pipeline, CDN edge, license-check service.
  Each emits Prometheus metrics and Loki logs (see `/grafana`).
- **Grafana Cloud** - hosts the dashboards and alert rules in `/grafana`,
  and is the single API surface the agent talks to for both alerting and
  raw metric/log queries (`/api/alertmanager/...`, `/api/ds/query`,
  `/api/annotations`).
- **Continuity agent** (`/agent`) - a Google ADK `Agent` whose tools
  (`/agent/tools`) wrap the Grafana API and the Postgres audit log. Gemini,
  via Vertex AI, drives the tool-calling loop (implicit, through ADK) and
  is also called explicitly once per incident in `correlate_signals` to
  produce a structured root-cause hypothesis. Deployed to Cloud Run
  (webhook-triggered, see `agent/server.py`) and/or Vertex AI Agent Engine
  (see `agent/deploy.py`).
- **Postgres** (`/db`) - `incidents` + `decisions` tables. Every
  detection/investigation/hypothesis/remediation/report step is a row in
  `decisions`, forming the audit trail.
- **Next.js dashboard** (`/frontend`) - read-only view over the same
  Postgres tables (via a read-only DB role), rendering the live reasoning
  trail.

## Data flow (one incident)

1. A Grafana alert rule fires (e.g. CDN 5xx rate > 5%).
2. The agent's detection step (`query_alerts`) sees it - polling on a
   schedule, or triggered by a Grafana webhook hitting
   `agent/server.py:/webhook/alert`.
3. `log_decision` creates an `incidents` row and a `detection` `decisions`
   row.
4. `fetch_logs` pulls Loki logs + Prometheus metrics for the affected
   service; another `decisions` row records what was gathered and why.
5. `correlate_signals` sends the alert + evidence to Gemini, gets back a
   structured hypothesis; recorded as a `hypothesis` decision.
6. `remediate` either executes an allowlisted action (and annotates the
   Grafana dashboard) or files a report for a human; recorded as a
   `remediation` decision.
7. A final `report` decision summarizes the incident end-to-end.
8. The dashboard shows all of this, live, from Postgres.

## Where Gemini / Vertex AI is called

- `agent/agent.py` - `root_agent`'s `model=` wires the whole ADK
  tool-calling loop to Gemini via Vertex AI; every tool-selection turn is a
  live Vertex AI call made by the ADK runtime.
- `agent/tools/correlate_signals.py` - an explicit `google-genai` call
  (`genai.Client(vertexai=True, ...).models.generate_content(...)`) used to
  produce the structured root-cause hypothesis.
- `agent/deploy.py` - deploys `root_agent` to Vertex AI Agent Engine via
  `vertexai.agent_engines.create`.

## Where Grafana is called

- `agent/grafana_client.py` - all Grafana HTTP API calls
  (`/api/alertmanager/.../alerts`, `/api/ds/query` for both Prometheus and
  Loki, `/api/annotations`).
- `agent/tools/query_alerts.py`, `agent/tools/fetch_logs.py`,
  `agent/tools/remediate.py` - the ADK tools that call into
  `grafana_client.py`.
