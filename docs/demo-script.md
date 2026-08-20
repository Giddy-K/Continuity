# Demo script notes

Rough beats for a live/recorded demo, aimed at the Grafana track judging
criteria (real Grafana usage, real Gemini/Vertex AI usage, autonomous
loop, auditable trail).

## Setup before recording

1. Grafana Cloud stack open in one tab, showing the three dashboards
   (`/grafana/dashboards`) with live-ish data.
2. Next.js dashboard (`frontend`, `npm run dev`) open in another tab,
   empty state ("No incidents recorded yet").
3. Agent running (`adk web` for trace visibility, or the Cloud Run
   webhook server) with logs visible in a terminal.

## Beats

1. **Trigger the anomaly.** Push a synthetic spike into the demo
   metrics/logs (e.g. bump `cdn_requests_total{status="503"}` or whatever
   the load generator exposes) so a Grafana alert rule fires.
2. **Show the Grafana alert firing** in the Grafana UI - this is the
   ground truth the agent is reacting to, not something faked.
3. **Trigger/observe the agent run** - either via the Grafana alert
   webhook hitting `agent/server.py`, or by kicking off a run manually in
   `adk web`. Narrate the tool calls as they happen: `query_alerts` →
   `fetch_logs` → `correlate_signals` → `remediate` → `log_decision` at
   each step.
4. **Point out the explicit Gemini call** in `correlate_signals` output -
   read the returned hypothesis/confidence/recommended_action out loud.
5. **Show the bounded remediation** - either the action executed (and the
   resulting annotation appearing on the Grafana dashboard) or, if
   confidence was low, the incident report filed instead. Emphasize the
   allowlist in `remediate.py` as the safety boundary.
6. **Switch to the Next.js dashboard** - refresh, show the new incident
   and its full reasoning trail, step by step, matching what was narrated
   in beat 3.
7. **Close on the audit trail** - this is the differentiator: not just "an
   agent did something" but a complete, inspectable record of why.

## Fallback if live demo breaks

Keep a pre-recorded run's Postgres data (`db/schema.sql` + a seed dump) so
the frontend can still show a populated reasoning trail even if the live
Grafana → agent → Gemini path has a hiccup during recording.
