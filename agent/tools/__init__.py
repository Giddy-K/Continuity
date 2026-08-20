"""ADK tool functions the Continuity agent can call.

Each module exposes one plain Python function with a docstring and typed
signature - ADK's `google.adk.tools` layer introspects both to build the
function-calling schema handed to Gemini, so keep the docstrings accurate;
they are effectively the tool's API contract for the model.
"""

from .correlate_signals import correlate_signals
from .fetch_logs import fetch_logs
from .log_decision import log_decision
from .query_alerts import query_alerts
from .remediate import remediate

ALL_TOOLS = [query_alerts, fetch_logs, correlate_signals, remediate, log_decision]

__all__ = [
    "query_alerts",
    "fetch_logs",
    "correlate_signals",
    "remediate",
    "log_decision",
    "ALL_TOOLS",
]
