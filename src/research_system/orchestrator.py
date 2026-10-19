"""The orchestrator: an explicit state machine that runs the agents.

States and allowed transitions form the workflow DAG::

    idle -> planning -> researching -> analyzing -> reviewing -> writing
         -> completed
    any active state -> failed

Every agent invocation is wrapped with retry (up to ``max_retries``) and
every unit of work spends from a shared step budget; exhausting the budget
aborts the run cleanly into ``failed`` instead of looping. All of it is
written to the run trace, which ships inside the final report.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional

from .agents import (
    Agent,
    AgentContext,
    AnalystAgent,
    CriticAgent,
    PlannerAgent,
    ResearcherAgent,
    WriterAgent,
)
from .blackboard import Blackboard
from .config import OrchestratorConfig
from .connectors import ConnectorRegistry
from .models import ResearchReport, SourceDocument, VerificationSummary
from .trace import RunTrace


class BudgetExceeded(RuntimeError):
    """Raised when a run spends more steps than its budget allows."""


class OrchestrationError(RuntimeError):
    """Raised when a run fails after exhausting retries."""


class StateMachine:
    """Explicit transition table for the research workflow."""

    TRANSITIONS: dict[str, set[str]] = {
        "idle": {"planning", "failed"},
        "planning": {"researching", "failed"},
        "researching": {"analyzing", "failed"},
        "analyzing": {"reviewing", "failed"},
        "reviewing": {"writing", "failed"},
        "writing": {"completed", "failed"},
        "completed": set(),
        "failed": set(),
    }

    def __init__(self, trace: RunTrace):
        self.state = "idle"
        self._trace = trace

    def transition(self, to_state: str, agent: str = "orchestrator") -> None:
        if to_state not in self.TRANSITIONS[self.state]:
            raise OrchestrationError(
                f"illegal state transition {self.state} -> {to_state}"
            )
        previous = self.state
        self.state = to_state
        self._trace.record(to_state, agent, "transition", f"{previous} -> {to_state}")


class Orchestrator:
    """Runs one research question end to end and returns a verified report."""

    def __init__(
        self,
        config: OrchestratorConfig | None = None,
        registry: ConnectorRegistry | None = None,
        agents: dict[str, Agent] | None = None,
        now: Callable[[], str] | None = None,
    ):
        self.config = config or OrchestratorConfig()
        self.registry = registry or ConnectorRegistry()
        self._agents: dict[str, Agent] = agents or {
            "planning": PlannerAgent(),
            "researching": ResearcherAgent(),
            "analyzing": AnalystAgent(),
            "reviewing": CriticAgent(),
            "writing": WriterAgent(),
        }
        self._now = now or (lambda: datetime.now(timezone.utc).isoformat())
        self._steps_used = 0

    # -- budget ------------------------------------------------------------
    def _spend(self, n: int = 1) -> None:
        self._steps_used += n
        if self._steps_used > self.config.max_steps:
            raise BudgetExceeded(
                f"step budget exhausted: {self._steps_used} > {self.config.max_steps}"
            )

    # -- agent execution with retry ----------------------------------------
    def _run_agent(self, state: str, machine: StateMachine, ctx: AgentContext) -> None:
        agent = self._agents[state]
        attempts = 0
        while True:
            try:
                self._spend(1)
                ctx.trace.record(state, agent.name, "started")
                agent.run(ctx)
                ctx.trace.record(state, agent.name, "completed")
                return
            except BudgetExceeded:
                raise
            except Exception as exc:  # noqa: BLE001 - retry policy handles all agent errors
                attempts += 1
                ctx.trace.record(
                    state, agent.name, "error", f"attempt {attempts}: {exc}"
                )
                if attempts > self.config.max_retries:
                    raise OrchestrationError(
                        f"agent '{agent.name}' failed after {attempts} attempt(s): {exc}"
                    ) from exc
                ctx.trace.record(
                    state, agent.name, "retry", f"retrying ({attempts}/{self.config.max_retries})"
                )

    # -- main entry point ----------------------------------------------------
    def run(self, question: str, job_id: str = "job-0001") -> ResearchReport:
        self._steps_used = 0
        trace = RunTrace()
        machine = StateMachine(trace)
        blackboard = Blackboard(question)
        trace.record("idle", "orchestrator", "run_started", question)

        # Per-agent tool access: only researcher + critic receive the registry.
        contexts = {
            state: AgentContext(
                blackboard=blackboard,
                config=self.config,
                trace=trace,
                state=state,
                registry=self.registry if state in ("researching", "reviewing") else None,
                spend=self._spend,
            )
            for state in self._agents
        }

        try:
            for state in ("planning", "researching", "analyzing", "reviewing", "writing"):
                machine.transition(state)
                self._run_agent(state, machine, contexts[state])
            machine.transition("completed")
        except (BudgetExceeded, OrchestrationError) as exc:
            if machine.state not in ("completed", "failed"):
                machine.transition("failed")
            trace.record(machine.state, "orchestrator", "run_failed", str(exc))
            raise OrchestrationError(str(exc)) from exc

        sources = self._collect_sources(blackboard)
        report = ResearchReport(
            job_id=job_id,
            question=question,
            generated_at=self._now(),
            executive_summary=blackboard.executive_summary,
            sections=blackboard.sections,
            claims=blackboard.claims,
            sources=sources,
            verification=blackboard.verification_summary or VerificationSummary(),
            trace=trace.events,
        )
        trace.record("completed", "orchestrator", "report_ready", f"job {job_id}")
        report.trace = trace.events
        return report

    def _collect_sources(self, blackboard: Blackboard) -> list[SourceDocument]:
        seen: list[str] = []
        for claim in blackboard.claims:
            for sid in claim.source_ids:
                if sid not in seen:
                    seen.append(sid)
        docs = []
        for sid in seen:
            doc = self.registry.get(sid)
            if doc is not None:
                docs.append(doc)
        return docs
