"""Human-readable run trace.

Every state transition, agent start/finish, retry and budget event is
recorded with a sequence number, so a run can be audited end to end and
the trace ships inside the final report.
"""

from __future__ import annotations

from .models import TraceEvent


class RunTrace:
    def __init__(self):
        self._events: list[TraceEvent] = []

    def record(self, state: str, agent: str, event: str, detail: str = "") -> TraceEvent:
        entry = TraceEvent(
            seq=len(self._events) + 1,
            state=state,
            agent=agent,
            event=event,
            detail=detail,
        )
        self._events.append(entry)
        return entry

    @property
    def events(self) -> list[TraceEvent]:
        return list(self._events)

    def render(self) -> str:
        lines = []
        for e in self._events:
            suffix = f" — {e.detail}" if e.detail else ""
            lines.append(f"{e.seq:>3}. [{e.state:<11}] {e.agent:<11} {e.event}{suffix}")
        return "\n".join(lines)
