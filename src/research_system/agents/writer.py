"""Writer agent: composes the structured report from verified blackboard state.

The writer assembles an executive summary plus one section per research
aspect. Every claim sentence carries its citation marker (e.g. ``[2]``)
referencing the report bibliography, and flagged claims are rendered with
an explicit ⚠ marker rather than being hidden.
"""

from __future__ import annotations

from ..models import Claim, ReportSection, SourceDocument
from .base import Agent, AgentContext

ASPECT_HEADINGS = {
    "landscape": "Background and Current State",
    "evidence": "Evidence and Metrics",
    "operations": "Operational Signals",
    "risks": "Risks and Trade-offs",
    "actions": "Recommended Actions",
}


class WriterAgent(Agent):
    name = "writer"
    tools: tuple[str, ...] = ("blackboard.read", "blackboard.write")

    def run(self, ctx: AgentContext) -> None:
        bb = ctx.blackboard
        claims_by_aspect: dict[str, list[Claim]] = {}
        for claim in bb.claims:
            claims_by_aspect.setdefault(claim.aspect, []).append(claim)

        source_order = self._bibliography_order(bb.claims)
        cite = {sid: i + 1 for i, sid in enumerate(source_order)}

        sections: list[ReportSection] = []
        for aspect, heading in ASPECT_HEADINGS.items():
            aspect_claims = claims_by_aspect.get(aspect, [])
            if not aspect_claims:
                continue
            lines = []
            for claim in aspect_claims:
                marker = "".join(f"[{cite[sid]}]" for sid in claim.source_ids if sid in cite)
                flag = " ⚠ *(unverified — see Verification)*" if claim.verified is False else ""
                lines.append(f"- {claim.text} {marker}{flag}")
            sections.append(
                ReportSection(
                    heading=heading,
                    body_md="\n".join(lines),
                    claim_ids=[c.id for c in aspect_claims],
                )
            )
        bb.set_sections(sections)

        top_claims = [c for c in bb.claims if c.verified is not False][:3]
        highlights = " ".join(c.text for c in top_claims)
        summary = (
            f"This report answers the question: “{bb.question}” "
            f"It is based on {len(bb.claims)} evidence-backed claims drawn from "
            f"{len(source_order)} sources across documents, tickets and metrics. "
            f"Key findings: {highlights}"
        )
        bb.executive_summary = summary
        bb.note(self.name, f"composed {len(sections)} sections")

    @staticmethod
    def _bibliography_order(claims: list[Claim]) -> list[str]:
        seen: list[str] = []
        for claim in claims:
            for sid in claim.source_ids:
                if sid not in seen:
                    seen.append(sid)
        return seen
