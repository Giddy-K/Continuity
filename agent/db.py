"""Postgres access for the incident + decision audit trail.

Every step the agent takes (detection, investigation, hypothesis,
remediation, report) is written here via `log_decision`. The Next.js
frontend reads this same table read-only to render the live reasoning
trail - see /db/schema.sql for the table definitions.
"""

from __future__ import annotations

import json
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from config import get_settings


@contextmanager
def get_connection() -> Generator[psycopg.Connection]:
    settings = get_settings()
    conn = psycopg.connect(settings.database_url, row_factory=dict_row)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_incident(
    title: str,
    severity: str,
    source_alert: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """Insert a new incident row, returning its id."""
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO incidents (title, severity, source_alert, metadata)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (title, severity, source_alert, json.dumps(metadata or {})),
        ).fetchone()
        return str(row["id"])


def record_decision(
    incident_id: str,
    step: str,
    reasoning: str,
    action_taken: str | None = None,
    action_result: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
) -> str:
    """Append one auditable step to an incident's reasoning trail.

    `step` is one of: detection, investigation, hypothesis, remediation, report.
    """
    with get_connection() as conn:
        row = conn.execute(
            """
            INSERT INTO decisions (incident_id, step, reasoning, action_taken, action_result, tool_calls)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (incident_id, step, reasoning, action_taken, action_result, json.dumps(tool_calls or [])),
        ).fetchone()
        return str(row["id"])


def close_incident(incident_id: str, status: str = "resolved") -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE incidents SET status = %s, resolved_at = now() WHERE id = %s",
            (status, incident_id),
        )
