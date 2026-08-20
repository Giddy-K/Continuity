import { listIncidents } from "@/lib/db";

export const dynamic = "force-dynamic"; // always show the latest incidents

export default async function Home() {
  let incidents: Awaited<ReturnType<typeof listIncidents>> = [];
  let error: string | null = null;

  try {
    incidents = await listIncidents();
  } catch (err) {
    error = err instanceof Error ? err.message : "Failed to load incidents";
  }

  return (
    <main style={{ maxWidth: 860, margin: "0 auto", padding: "2rem 1.5rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Continuity</h1>
      <p style={{ color: "#666" }}>
        Read-only reasoning-trail dashboard. This is a placeholder view - it lists
        incidents from the audit trail the agent writes via <code>agent/tools/log_decision.py</code>.
      </p>

      {error && (
        <p style={{ color: "#b91c1c", background: "#fef2f2", padding: "0.75rem 1rem", borderRadius: 6 }}>
          Could not load incidents: {error}. Set <code>DATABASE_URL_READONLY</code> in{" "}
          <code>frontend/.env.local</code> (see <code>frontend/.env.example</code>).
        </p>
      )}

      {!error && incidents.length === 0 && <p>No incidents recorded yet.</p>}

      <ul style={{ listStyle: "none", padding: 0 }}>
        {incidents.map((incident) => (
          <li
            key={incident.id}
            style={{ border: "1px solid #e5e5e5", borderRadius: 8, padding: "1rem", marginBottom: "0.75rem" }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
              <strong>{incident.title}</strong>
              <span style={{ fontSize: "0.85rem", color: "#666" }}>{incident.status}</span>
            </div>
            <div style={{ fontSize: "0.85rem", color: "#666" }}>
              severity: {incident.severity} · detected: {new Date(incident.detected_at).toLocaleString()}
            </div>
            {incident.root_cause_hypothesis && <p style={{ marginBottom: 0 }}>{incident.root_cause_hypothesis}</p>}
          </li>
        ))}
      </ul>
    </main>
  );
}
