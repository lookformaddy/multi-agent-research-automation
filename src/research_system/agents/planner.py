"""Planner agent: decomposes the research question into subtasks.

The decomposition is aspect-based and deterministic: every question is
researched from the same five angles (landscape, evidence, operations,
risks, actions), and each aspect contributes search terms that steer the
researcher's retrieval. In an LLM-backed deployment this agent is where a
model would propose a bespoke plan; the aspect scaffold stays as the
guardrail that keeps plans complete and comparable across runs.
"""

from __future__ import annotations

from ..models import SubTask
from ..text import tokenize
from .base import Agent, AgentContext

ASPECTS: list[tuple[str, str, str]] = [
    # (aspect, title template, extra steering terms)
    ("landscape", "Current state and background", "overview guide explained review"),
    ("evidence", "Quantitative evidence", "metrics data percent spend volume rate"),
    ("operations", "Operational signals and incidents", "ticket incident report issue audit"),
    ("risks", "Risks, trade-offs and constraints", "risk trade-off failure budget reliability"),
    ("actions", "Recommended actions", "recommend should action improve reduce propose"),
]


class PlannerAgent(Agent):
    name = "planner"
    tools: tuple[str, ...] = ()  # planning needs no source access

    def run(self, ctx: AgentContext) -> None:
        question = ctx.blackboard.question
        focus_terms = tokenize(question)
        if not focus_terms:
            raise ValueError("question contains no searchable terms")
        focus = " ".join(focus_terms[:8])
        plan: list[SubTask] = []
        for idx, (aspect, title, steering) in enumerate(ASPECTS, start=1):
            plan.append(
                SubTask(
                    id=f"task-{idx}",
                    aspect=aspect,
                    title=f"{title}: {question.rstrip('?')}",
                    query=f"{focus} {steering}",
                )
            )
        ctx.blackboard.set_plan(plan)
        ctx.blackboard.note(
            self.name,
            f"decomposed question into {len(plan)} subtasks over aspects "
            + ", ".join(a for a, _, _ in ASPECTS),
        )
