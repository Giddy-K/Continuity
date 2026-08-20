# Continuity frontend

Next.js (App Router) dashboard giving a read-only view into the agent's
reasoning trail, stored in Postgres by `agent/db.py` /
`agent/tools/log_decision.py`.

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local   # fill in DATABASE_URL_READONLY
npm run dev
```

Visit http://localhost:3000 - it lists recent incidents from the
`incidents` table. `app/api/incidents/route.ts` exposes the same data as
JSON for future use (e.g. client-side polling for live updates, or a
per-incident detail view pulling from `decisions`).

This is currently a placeholder: a single page listing incidents. Not yet
built: per-incident decision timeline view, live updates (poll or
websocket), auth in front of the dashboard if deployed publicly.
