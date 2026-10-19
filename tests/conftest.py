"""Shared fixtures: a fixed clock makes runs byte-for-byte deterministic."""

import pytest

from research_system.orchestrator import Orchestrator

FIXED_TIME = "2026-01-15T12:00:00+00:00"
DEMO_QUESTION = "How can we reduce cloud infrastructure costs without hurting reliability?"


@pytest.fixture
def orchestrator() -> Orchestrator:
    return Orchestrator(now=lambda: FIXED_TIME)


@pytest.fixture
def report(orchestrator: Orchestrator):
    return orchestrator.run(DEMO_QUESTION, job_id="job-test-0001")
