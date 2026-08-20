-- Current full schema, generated from db/migrations/*.sql in order.
-- Convenience file for quickly standing up a fresh dev database:
--   createdb continuity && psql continuity -f db/schema.sql
-- The source of truth is the migrations directory; keep this in sync
-- whenever a new migration is added.

\ir migrations/001_init.sql
