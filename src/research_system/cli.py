"""Command-line demo: run one research question end to end.

Usage:
    python -m research_system.cli "How can we reduce cloud infrastructure costs?"
    research-system "How can we reduce support ticket volume?" --out out/ --trace

Writes ``report.json`` and ``report.md`` into ``--out`` when given, and
prints the Markdown report to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import OrchestratorConfig
from .orchestrator import OrchestrationError, Orchestrator
from .report import render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="research-system",
        description="Multi-agent research & automation system (offline demo).",
    )
    parser.add_argument("question", help="The research question to answer.")
    parser.add_argument("--out", type=Path, default=None, help="Directory for report.json/report.md.")
    parser.add_argument("--top-k", type=int, default=3, help="Passages retrieved per subtask.")
    parser.add_argument("--max-steps", type=int, default=60, help="Orchestrator step budget.")
    parser.add_argument("--job-id", default="job-cli-0001", help="Job id stamped on the report.")
    parser.add_argument("--trace", action="store_true", help="Also print the run trace.")
    args = parser.parse_args(argv)

    config = OrchestratorConfig(max_steps=args.max_steps, top_k=args.top_k)
    orchestrator = Orchestrator(config=config)
    try:
        report = orchestrator.run(args.question, job_id=args.job_id)
    except OrchestrationError as exc:
        print(f"run failed: {exc}", file=sys.stderr)
        return 1

    markdown = render_markdown(report)
    print(markdown)
    if args.trace:
        print("\n--- run trace ---\n")
        for e in report.trace:
            suffix = f" — {e.detail}" if e.detail else ""
            print(f"{e.seq:>3}. [{e.state:<11}] {e.agent:<11} {e.event}{suffix}")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "report.md").write_text(markdown, encoding="utf-8")
        (args.out / "report.json").write_text(
            json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8"
        )
        print(f"\nwrote {args.out / 'report.md'} and {args.out / 'report.json'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
