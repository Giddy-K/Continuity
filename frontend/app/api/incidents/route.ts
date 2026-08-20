import { NextResponse } from "next/server";
import { listIncidents } from "@/lib/db";

// Read-only endpoint backing the dashboard: returns recent incidents from
// the audit trail the agent writes via agent/tools/log_decision.py.
export async function GET() {
  try {
    const incidents = await listIncidents();
    return NextResponse.json({ incidents });
  } catch (err) {
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed to load incidents" },
      { status: 500 }
    );
  }
}
