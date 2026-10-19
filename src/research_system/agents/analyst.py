"""Analyst agent: turns retrieved passages into claims.

Claims are deliberately *extractive*: each claim is the single most
relevant sentence of a cited passage, so every assertion in the report is
traceable to source text the critic can re-check word by word. The analyst
also records coverage notes (which aspects found no evidence) that the
writer surfaces honestly in the report instead of papering over gaps.
"""

from __future__ import annotations

from ..models import Claim
from .base import Agent, AgentContext


class AnalystAgent(Agent):
    name = "analyst"
    tools: tuple[str, ...] = ("blackboard.read", "blackboard.write")

    def run(self, ctx: AgentContext) -> None:
        claims: list[Claim] = []
        seen_texts: set[str] = set()
        for finding in ctx.blackboard.findings:
            if not finding.passages:
                ctx.blackboard.note(
                    self.name,
                    f"no evidence found for subtask {finding.subtask_id} "
                    f"({finding.aspect}); coverage gap recorded",
                )
                continue
            for passage in finding.passages[: ctx.config.max_claims_per_finding]:
                if passage.excerpt in seen_texts:
                    continue  # same evidence already claimed under another aspect
                seen_texts.add(passage.excerpt)
                claims.append(
                    Claim(
                        id=f"claim-{len(claims) + 1:02d}",
                        text=passage.excerpt,
                        aspect=finding.aspect,
                        source_ids=[passage.source_id],
                    )
                )
        if not claims:
            raise ValueError("no evidence-backed claims could be produced")
        ctx.blackboard.set_claims(claims)
        ctx.blackboard.note(self.name, f"produced {len(claims)} extractive claims")
