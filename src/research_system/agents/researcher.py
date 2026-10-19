"""Researcher agent: gathers cited evidence for every planned subtask.

This is the only agent with connector access. For each subtask it searches
all registered connectors, deduplicates passages by source, and publishes
a ``Finding`` to the blackboard. Each search consumes step budget, so a
runaway plan cannot loop forever.
"""

from __future__ import annotations

from ..models import Finding, Passage
from ..text import best_sentence, split_sentences, tokenize
from .base import Agent, AgentContext


class ResearcherAgent(Agent):
    name = "researcher"
    tools: tuple[str, ...] = ("connectors.search",)

    def run(self, ctx: AgentContext) -> None:
        registry = ctx.require_registry()
        plan = ctx.blackboard.plan
        if not plan:
            raise ValueError("researcher ran before the planner produced a plan")
        used_excerpts: set[str] = set()
        for subtask in plan:
            ctx.spend(1)  # one step per subtask search; may raise BudgetExceeded
            passages = registry.search_all(subtask.query, top_k=ctx.config.top_k)
            deduped: list[Passage] = []
            seen: set[str] = set()
            for passage in passages:
                if passage.source_id in seen:
                    continue
                seen.add(passage.source_id)
                if passage.excerpt in used_excerpts:
                    # This source already contributed that sentence to an
                    # earlier subtask: offer its next-best distinct sentence
                    # for this subtask's angle instead of repeating text.
                    doc = registry.get(passage.source_id)
                    remaining = [
                        s
                        for s in split_sentences(doc.body if doc else "")
                        if s not in used_excerpts
                    ]
                    if not remaining:
                        continue
                    excerpt = best_sentence(
                        " ".join(remaining), tokenize(subtask.query)
                    )
                    passage = passage.model_copy(update={"excerpt": excerpt})
                used_excerpts.add(passage.excerpt)
                deduped.append(passage)
            ctx.blackboard.add_finding(
                Finding(subtask_id=subtask.id, aspect=subtask.aspect, passages=deduped)
            )
            ctx.trace.record(
                ctx.state,
                self.name,
                "retrieved",
                f"{subtask.id} ({subtask.aspect}): {len(deduped)} passages",
            )
        ctx.blackboard.note(
            self.name,
            f"gathered evidence for {len(plan)} subtasks across "
            f"{len(registry.connectors)} connectors",
        )
