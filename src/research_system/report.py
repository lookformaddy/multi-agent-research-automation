"""Render a ResearchReport as Markdown (the JSON form is the model itself)."""

from __future__ import annotations

from .models import ResearchReport


def render_markdown(report: ResearchReport) -> str:
    lines: list[str] = []
    lines.append(f"# Research Report: {report.question}")
    lines.append("")
    lines.append(f"*Job `{report.job_id}` · Generated {report.generated_at}*")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(report.executive_summary)
    lines.append("")
    for section in report.sections:
        lines.append(f"## {section.heading}")
        lines.append("")
        lines.append(section.body_md)
        lines.append("")
    lines.append("## Verification & Confidence")
    lines.append("")
    v = report.verification
    lines.append(f"- Claims checked: **{v.total_claims}**")
    lines.append(f"- Verified against sources: **{v.verified_claims}**")
    lines.append(f"- Flagged as unsupported: **{v.flagged_claims}**")
    lines.append(f"- Overall confidence: **{v.confidence:.0%}** (verified / total)")
    if v.flagged_claim_ids:
        lines.append(f"- Flagged claim ids: {', '.join(v.flagged_claim_ids)}")
    lines.append("")
    lines.append(f"Method: {v.method}")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    for idx, source in enumerate(report.sources, start=1):
        lines.append(f"{idx}. **{source.title}** (`{source.id}`, {source.kind.value})")
    lines.append("")
    lines.append("## Claim Audit Trail")
    lines.append("")
    lines.append("| Claim | Support | Verified | Flags |")
    lines.append("|---|---|---|---|")
    for claim in report.claims:
        flags = ", ".join(claim.flags) if claim.flags else "—"
        lines.append(
            f"| {claim.id} | {claim.support_score:.2f} | "
            f"{'yes' if claim.verified else 'no'} | {flags} |"
        )
    lines.append("")
    return "\n".join(lines)
