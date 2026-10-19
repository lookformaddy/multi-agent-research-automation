"""Multi-Agent Research & Automation System.

An orchestrator runs specialized agents (planner, researcher, analyst,
writer, critic) as an explicit state machine over a shared blackboard.
Agents retrieve evidence from pluggable source connectors with citations,
and a critic agent verifies every claim against its sources before a
structured report (JSON + Markdown) is produced.
"""

__version__ = "0.1.0"
