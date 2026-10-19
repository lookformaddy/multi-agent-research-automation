"""Pydantic schemas shared by agents, the orchestrator, the API and the CLI."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SourceKind(str, Enum):
    DOC = "doc"
    TICKET = "ticket"
    METRIC = "metric"


class SourceDocument(BaseModel):
    """One retrievable item in a source corpus."""

    id: str
    kind: SourceKind
    title: str
    body: str
    tags: list[str] = Field(default_factory=list)


class Passage(BaseModel):
    """A retrieved excerpt, permanently tied to its source for citation."""

    source_id: str
    source_title: str
    kind: SourceKind
    excerpt: str
    score: float


class SubTask(BaseModel):
    """One slice of the research question, produced by the planner."""

    id: str
    aspect: str
    title: str
    query: str


class Finding(BaseModel):
    """Researcher output for one subtask: the evidence it gathered."""

    subtask_id: str
    aspect: str
    passages: list[Passage] = Field(default_factory=list)


class Claim(BaseModel):
    """A single assertion in the report, with the sources that back it.

    The critic fills in ``verified``, ``support_score`` and ``flags``.
    """

    id: str
    text: str
    aspect: str = "landscape"
    source_ids: list[str] = Field(default_factory=list)
    verified: Optional[bool] = None
    support_score: float = 0.0
    flags: list[str] = Field(default_factory=list)


class ReportSection(BaseModel):
    heading: str
    body_md: str
    claim_ids: list[str] = Field(default_factory=list)


class VerificationSummary(BaseModel):
    total_claims: int = 0
    verified_claims: int = 0
    flagged_claims: int = 0
    confidence: float = 0.0
    flagged_claim_ids: list[str] = Field(default_factory=list)
    method: str = (
        "Each claim is checked against the full text of its cited sources: "
        "citations must resolve, and at least the configured fraction of the "
        "claim's content terms must appear in the cited sources."
    )


class TraceEvent(BaseModel):
    seq: int
    state: str
    agent: str
    event: str
    detail: str = ""


class ResearchReport(BaseModel):
    job_id: str
    question: str
    generated_at: str
    executive_summary: str
    sections: list[ReportSection] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    sources: list[SourceDocument] = Field(default_factory=list)
    verification: VerificationSummary = Field(default_factory=VerificationSummary)
    trace: list[TraceEvent] = Field(default_factory=list)


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchJob(BaseModel):
    id: str
    question: str
    status: JobStatus = JobStatus.QUEUED
    created_at: str = ""
    report: Optional[ResearchReport] = None
    error: Optional[str] = None


class JobRequest(BaseModel):
    question: str = Field(min_length=8, description="The research question to answer.")
    max_steps: Optional[int] = Field(
        default=None, ge=1, description="Override the orchestrator step budget."
    )
    top_k: Optional[int] = Field(
        default=None, ge=1, le=10, description="Passages retrieved per subtask."
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
