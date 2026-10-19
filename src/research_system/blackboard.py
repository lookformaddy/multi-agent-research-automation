"""The shared blackboard: how agents communicate.

Agents never call each other directly. Each agent reads what it needs from
the blackboard and publishes its output back to well-known keys, which keeps
the workflow inspectable (the blackboard is dumped into the run trace on
request) and lets the orchestrator retry or replace an agent without
rewiring the others.
"""

from __future__ import annotations

from typing import Any

from .models import Claim, Finding, ReportSection, SubTask, VerificationSummary


class Blackboard:
    KEYS = ("question", "plan", "findings", "claims", "sections", "notes")

    # Filled by the critic / writer respectively, read by the orchestrator.
    verification_summary: VerificationSummary | None = None
    executive_summary: str = ""

    def __init__(self, question: str):
        self._data: dict[str, Any] = {
            "question": question,
            "plan": [],
            "findings": [],
            "claims": [],
            "sections": [],
            "notes": [],
        }

    @property
    def question(self) -> str:
        return self._data["question"]

    # -- plan ------------------------------------------------------------
    def set_plan(self, plan: list[SubTask]) -> None:
        self._data["plan"] = list(plan)

    @property
    def plan(self) -> list[SubTask]:
        return self._data["plan"]

    # -- findings ----------------------------------------------------------
    def add_finding(self, finding: Finding) -> None:
        self._data["findings"].append(finding)

    @property
    def findings(self) -> list[Finding]:
        return self._data["findings"]

    # -- claims ------------------------------------------------------------
    def set_claims(self, claims: list[Claim]) -> None:
        self._data["claims"] = list(claims)

    @property
    def claims(self) -> list[Claim]:
        return self._data["claims"]

    # -- sections ----------------------------------------------------------
    def set_sections(self, sections: list[ReportSection]) -> None:
        self._data["sections"] = list(sections)

    @property
    def sections(self) -> list[ReportSection]:
        return self._data["sections"]

    # -- free-form agent notes --------------------------------------------
    def note(self, agent: str, message: str) -> None:
        self._data["notes"].append(f"{agent}: {message}")

    @property
    def notes(self) -> list[str]:
        return list(self._data["notes"])

    def snapshot(self) -> dict[str, Any]:
        return {
            "plan": [t.id for t in self.plan],
            "findings": {f.subtask_id: len(f.passages) for f in self.findings},
            "claims": len(self.claims),
            "sections": [s.heading for s in self.sections],
            "notes": self.notes,
        }
