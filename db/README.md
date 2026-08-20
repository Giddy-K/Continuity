# Database

Postgres schema for the incident + decision audit trail that both the
agent (`agent/db.py`) and the frontend (`frontend/`) read/write.

## Tables

- **incidents** - one row per detected incident (title, severity, status,
  the Grafana alert that triggered it, timestamps).
- **decisions** - one row per reasoning step the agent takes on an
  incident (`detection`, `investigation`, `hypothesis`, `remediation`,
  `report`), each with the agent's own explanation in `reasoning` plus any
  `action_taken` / `action_result`. This table is the audit trail /
  reasoning-trail data source.

## Local setup

```bash
createdb continuity
psql continuity -f db/schema.sql
```

## Migrations

Plain numbered `.sql` files in `migrations/`, applied in order with
`psql "$DATABASE_URL" -f db/migrations/NNN_name.sql`. No migration
framework yet - add one (e.g. `dbmate`, `sqlx-cli`, Alembic) if this grows
past a handful of files.
