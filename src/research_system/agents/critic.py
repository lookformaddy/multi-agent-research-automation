"""Critic agent: verifies every claim against its cited sources.

For each claim the critic checks that (1) every citation resolves to a
real source, and (2) at least ``min_claim_support`` of the claim's content
terms actually appear in the cited sources' full text. Claims that fail
are flagged — never silently dropped — and the writer's confidence section
reports the verified/total ratio. This is the guardrail that keeps an
automation pipeline from laundering guesses into 'findings'.
"""

from __future__ import annotations

from ..models import VerificationSummary
from ..text import tokenize
from .base import Agent, AgentContext


class CriticAgent(Agent):
    name = "critic"
    tools: tuple[str, ...] = ("connectors.lookup",)

    def run(self, ctx: AgentContext) -> VerificationSummary:
        registry = ctx.require_registry()
        claims = ctx.blackboard.claims
        flagged_ids: list[str] = []
        verified_count = 0
        for claim in claims:
            flags: list[str] = []
            if not claim.source_ids:
                flags.append("no_citation")
            source_terms: set[str] = set()
            for source_id in claim.source_ids:
                doc = registry.get(source_id)
                if doc is None:
                    flags.append(f"unresolvable_citation:{source_id}")
                else:
                    source_terms |= set(tokenize(f"{doc.title} {doc.body}"))
            claim_terms = set(tokenize(claim.text))
            if claim_terms:
                overlap = len(claim_terms & source_terms) / len(claim_terms)
            else:
                overlap = 0.0
            claim.support_score = round(overlap, 3)
            if claim.source_ids and overlap < ctx.config.min_claim_support:
                flags.append("unsupported_by_sources")
            claim.flags = flags
            claim.verified = not flags
            if claim.verified:
                verified_count += 1
            else:
                flagged_ids.append(claim.id)
            ctx.trace.record(
                ctx.state,
                self.name,
                "verified" if claim.verified else "flagged",
                f"{claim.id}: support={claim.support_score:.2f}"
                + (f" flags={','.join(flags)}" if flags else ""),
            )
        summary = VerificationSummary(
            total_claims=len(claims),
            verified_claims=verified_count,
            flagged_claims=len(claims) - verified_count,
            confidence=round(verified_count / len(claims), 3) if claims else 0.0,
            flagged_claim_ids=flagged_ids,
        )
        ctx.blackboard.note(
            self.name,
            f"verified {verified_count}/{len(claims)} claims "
            f"(confidence {summary.confidence:.0%})",
        )
        ctx.blackboard.verification_summary = summary
        return summary
