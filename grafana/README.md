# Grafana assets

This directory holds the observability config for the simulated media
studio infra that Continuity watches.

- `dashboards/` - dashboard JSON exports (importable via Grafana's UI or
  the dashboards API) covering the three signal sources named in the
  concept: render pipeline latency, CDN error rates, and license-check
  failures.
- `alerting/alert_rules.yaml` - Grafana unified alerting rules, provisioned
  via the [alerting provisioning
  API](https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/).
  These are what fire the alerts `agent/tools/query_alerts.py` polls.
- `provisioning/prometheus.yml`, `provisioning/promtail.yml` - scrape/push
  configs for a local Prometheus + Promtail pair remote-writing into
  Grafana Cloud's managed Mimir/Loki, standing in for real render-farm,
  CDN, and license-check telemetry during the demo.

## Wiring it up

1. Create a Grafana Cloud stack (or use an existing one).
2. Fill in `GRAFANA_URL` / `GRAFANA_API_KEY` in your `.env` (see
   `.env.example` at the repo root) with a Grafana Cloud service account
   token that has `Alerting: Reader`, `Datasources: Reader`, and
   `Annotations: Writer` permissions at minimum.
3. Import the dashboards in `dashboards/` and the alert rules in
   `alerting/alert_rules.yaml`.
4. Point `provisioning/prometheus.yml` / `provisioning/promtail.yml` at
   your stack's remote-write / push endpoints (found under Grafana Cloud's
   "Connections > Add new connection > Hosted Prometheus/Loki metrics"
   pages) and run them alongside whatever emits the demo's synthetic
   render/CDN/license-check metrics and logs.
5. Grab the Prometheus and Loki datasource UIDs from Grafana (Connections >
   Data sources) and set `GRAFANA_PROMETHEUS_DATASOURCE_UID` /
   `GRAFANA_LOKI_DATASOURCE_UID`.
