import pytest

from research_system.agents import PlannerAgent
from research_system.blackboard import Blackboard
from research_system.agents.base import AgentContext
from research_system.config import OrchestratorConfig
from research_system.trace import RunTrace


def _planner_ctx(question: str) -> AgentContext:
    return AgentContext(
        blackboard=Blackboard(question),
        config=OrchestratorConfig(),
        trace=RunTrace(),
        state="planning",
        registry=None,
    )


def test_planner_decomposes_into_five_aspects():
    ctx = _planner_ctx("How can we reduce cloud infrastructure costs?")
    PlannerAgent().run(ctx)
    aspects = [t.aspect for t in ctx.blackboard.plan]
    assert aspects == ["landscape", "evidence", "operations", "risks", "actions"]
    assert all(t.query for t in ctx.blackboard.plan)
    assert len({t.id for t in ctx.blackboard.plan}) == 5


def test_planner_queries_carry_question_terms():
    ctx = _planner_ctx("How can we reduce support ticket volume?")
    PlannerAgent().run(ctx)
    assert all("support" in t.query and "ticket" in t.query for t in ctx.blackboard.plan)


def test_planner_rejects_empty_question():
    ctx = _planner_ctx("???")
    with pytest.raises(ValueError):
        PlannerAgent().run(ctx)


def test_blackboard_snapshot_reflects_state():
    ctx = _planner_ctx("How can we cut churn?")
    PlannerAgent().run(ctx)
    snap = ctx.blackboard.snapshot()
    assert snap["plan"] == ["task-1", "task-2", "task-3", "task-4", "task-5"]
    assert snap["claims"] == 0
