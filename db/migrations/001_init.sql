-- Continuity: incident + decision audit trail
-- Applied via: psql "$DATABASE_URL" -f db/migrations/001_init.sql

CREATE EXTENSION IF NOT EXISTS pgcrypto; -- gen_random_uuid()

CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'
        CHECK (status IN ('open', 'investigating', 'remediated', 'resolved', 'closed')),
    severity TEXT NOT NULL
        CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    source_alert TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    root_cause_hypothesis TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    step TEXT NOT NULL
        CHECK (step IN ('detection', 'investigation', 'hypothesis', 'remediation', 'report')),
    reasoning TEXT NOT NULL,
    action_taken TEXT,
    action_result TEXT,
    tool_calls JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_decisions_incident_id ON decisions (incident_id);
CREATE INDEX IF NOT EXISTS idx_decisions_created_at ON decisions (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents (status);
CREATE INDEX IF NOT EXISTS idx_incidents_detected_at ON incidents (detected_at DESC);

-- Read-only role for the Next.js frontend dashboard (see /frontend).
-- Run manually with a real password; do not hardcode credentials in
-- committed SQL.
-- CREATE ROLE continuity_ro LOGIN PASSWORD '<set via Secret Manager>';
-- GRANT CONNECT ON DATABASE continuity TO continuity_ro;
-- GRANT USAGE ON SCHEMA public TO continuity_ro;
-- GRANT SELECT ON incidents, decisions TO continuity_ro;
