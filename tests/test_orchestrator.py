import pytest

from research_system.agents import Agent
from research_system.agents.base import AgentContext
from research_system.config import OrchestratorConfig
from research_system.orchestrator import OrchestrationError, Orchestrator

DEMO_QUESTION = "How can we reduce cloud infrastructure costs without hurting reliability?"


def test_full_run_completes_with_verified_report(report):
    assert report.question == DEMO_QUESTION
    assert report.generated_at == "2026-01-15T12:00:00+00:00"
    assert report.executive_summary
    assert len(report.sections) >= 3
    assert report.claims, "expected evidence-backed claims"
    v = report.verification
    assert v.total_claims == len(report.claims)
    assert v.verified_claims + v.flagged_claims == v.total_claims
    assert v.confidence == pytest.approx(v.verified_claims / v.total_claims)
    # Extractive claims must verify: every claim cites a real source.
    assert v.confidence >= 0.8
    for claim in report.claims:
        assert claim.source_ids
        assert all(sid in {s.id for s in report.sources} for sid in claim.source_ids)


def test_trace_shows_state_machine_order(report):
    transitions = [
        e.detail for e in report.trace if e.event == "transition" and "->" in e.detail
    ]
    assert transitions == [
        "idle -> planning",
        "planning -> researching",
        "researching -> analyzing",
        "analyzing -> reviewing",
        "reviewing -> writing",
        "writing -> completed",
    ]
    agents_seen = {e.agent for e in report.trace if e.event == "completed"}
    assert {"planner", "researcher", "analyst", "critic", "writer"} <= agents_seen


def test_run_is_deterministic(orchestrator):
    first = orchestrator.run(DEMO_QUESTION, job_id="job-a")
    second = orchestrator.run(DEMO_QUESTION, job_id="job-a")
    assert first.model_dump() == second.model_dump()


def test_step_budget_aborts_run():
    orchestrator = Orchestrator(
        config=OrchestratorConfig(max_steps=3), now=lambda: "t"
    )
    with pytest.raises(OrchestrationError, match="budget"):
        orchestrator.run(DEMO_QUESTION, job_id="job-budget")


class FlakyAgent(Agent):
    """Fails N times, then succeeds — exercises the retry policy."""

    name = "flaky"
    tools: tuple[str, ...] = ()

    def __init__(self, fail_times: int):
        self.fail_times = fail_times
        self.calls = 0

    def run(self, ctx: AgentContext) -> None:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("transient boom")
        # Minimal stand-in for the real planner.
        from research_system.agents import PlannerAgent

        PlannerAgent().run(ctx)


def _orchestrator_with_flaky_planner(fail_times: int) -> Orchestrator:
    from research_system.agents import (
        AnalystAgent,
        CriticAgent,
        ResearcherAgent,
        WriterAgent,
    )

    agents = {
        "planning": FlakyAgent(fail_times),
        "researching": ResearcherAgent(),
        "analyzing": AnalystAgent(),
        "reviewing": CriticAgent(),
        "writing": WriterAgent(),
    }
    return Orchestrator(agents=agents, now=lambda: "t")


def test_agent_retry_recovers_from_transient_failure():
    orchestrator = _orchestrator_with_flaky_planner(fail_times=1)
    report = orchestrator.run(DEMO_QUESTION, job_id="job-retry")
    assert report.claims
    events = [e.event for e in report.trace]
    assert "retry" in events


def test_agent_retry_exhaustion_fails_run():
    orchestrator = _orchestrator_with_flaky_planner(fail_times=99)
    with pytest.raises(OrchestrationError, match="failed after"):
        orchestrator.run(DEMO_QUESTION, job_id="job-doomed")
