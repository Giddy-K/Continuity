import { Pool } from "pg";

// Single shared read-only pool for the incident/decision audit trail.
// Reused across requests in the same server runtime instance.
let pool: Pool | undefined;

function getPool(): Pool {
  if (!pool) {
    const connectionString = process.env.DATABASE_URL_READONLY;
    if (!connectionString) {
      throw new Error(
        "Missing DATABASE_URL_READONLY. Copy frontend/.env.example to frontend/.env.local."
      );
    }
    pool = new Pool({ connectionString });
  }
  return pool;
}

export interface Incident {
  id: string;
  title: string;
  status: string;
  severity: string;
  source_alert: string | null;
  detected_at: string;
  resolved_at: string | null;
  root_cause_hypothesis: string | null;
}

export interface Decision {
  id: string;
  incident_id: string;
  step: string;
  reasoning: string;
  action_taken: string | null;
  action_result: string | null;
  created_at: string;
}

export async function listIncidents(limit = 50): Promise<Incident[]> {
  const { rows } = await getPool().query<Incident>(
    `SELECT id, title, status, severity, source_alert, detected_at, resolved_at, root_cause_hypothesis
     FROM incidents
     ORDER BY detected_at DESC
     LIMIT $1`,
    [limit]
  );
  return rows;
}

export async function listDecisionsForIncident(incidentId: string): Promise<Decision[]> {
  const { rows } = await getPool().query<Decision>(
    `SELECT id, incident_id, step, reasoning, action_taken, action_result, created_at
     FROM decisions
     WHERE incident_id = $1
     ORDER BY created_at ASC`,
    [incidentId]
  );
  return rows;
}
