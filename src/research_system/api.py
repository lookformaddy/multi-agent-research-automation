"""FastAPI service wrapper around the orchestrator.

Endpoints:
- ``POST /jobs``            submit a research question, run it, get the job
- ``GET  /jobs/{id}``       job status (+ report when completed)
- ``GET  /jobs/{id}/report`` the report as JSON (``?format=json``) or
                            Markdown (``?format=md``, plain text)
- ``GET  /jobs/{id}/trace`` the human-readable run trace
- ``GET  /sources``         the corpora available to the connectors
- ``GET  /health``          liveness

Runs execute synchronously: the bundled corpora are small and retrieval is
deterministic, so a job completes in milliseconds and polling is trivial.
The job store is in-memory; swap in a database + task queue for production
(see docs/architecture.md).
"""

from __future__ import annotations

import itertools

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse

from .config import OrchestratorConfig
from .connectors import ConnectorRegistry
from .models import JobRequest, JobStatus, ResearchJob
from .orchestrator import OrchestrationError, Orchestrator
from .report import render_markdown


def create_app(registry: ConnectorRegistry | None = None) -> FastAPI:
    app = FastAPI(
        title="Multi-Agent Research & Automation System",
        version="0.1.0",
        description="Planner/researcher/analyst/writer/critic agents producing "
        "citation-verified research reports over pluggable source connectors.",
    )
    registry = registry or ConnectorRegistry()
    jobs: dict[str, ResearchJob] = {}
    counter = itertools.count(1)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "sources": len(registry.all_documents())}

    @app.get("/sources")
    def sources() -> list[dict]:
        return [
            {"id": d.id, "kind": d.kind.value, "title": d.title, "tags": d.tags}
            for d in registry.all_documents()
        ]

    @app.post("/jobs", status_code=201)
    def submit_job(request: JobRequest) -> ResearchJob:
        job_id = f"job-{next(counter):04d}"
        job = ResearchJob(id=job_id, question=request.question, status=JobStatus.RUNNING)
        jobs[job_id] = job
        config = OrchestratorConfig()
        if request.max_steps is not None:
            config.max_steps = request.max_steps
        if request.top_k is not None:
            config.top_k = request.top_k
        orchestrator = Orchestrator(config=config, registry=registry)
        try:
            report = orchestrator.run(request.question, job_id=job_id)
            job.report = report
            job.created_at = report.generated_at
            job.status = JobStatus.COMPLETED
        except OrchestrationError as exc:
            job.status = JobStatus.FAILED
            job.error = str(exc)
        return job

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str) -> ResearchJob:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        return job

    @app.get("/jobs/{job_id}/report")
    def get_report(job_id: str, format: str = Query(default="json", pattern="^(json|md)$")):
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        if job.status != JobStatus.COMPLETED or job.report is None:
            raise HTTPException(
                status_code=409,
                detail=f"job is {job.status.value}; no report available",
            )
        if format == "md":
            return PlainTextResponse(
                render_markdown(job.report), media_type="text/markdown"
            )
        return job.report

    @app.get("/jobs/{job_id}/trace", response_class=PlainTextResponse)
    def get_trace(job_id: str) -> str:
        job = jobs.get(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="job not found")
        if job.report is None:
            raise HTTPException(status_code=409, detail="no trace available")
        return "\n".join(
            f"{e.seq:>3}. [{e.state:<11}] {e.agent:<11} {e.event}"
            + (f" — {e.detail}" if e.detail else "")
            for e in job.report.trace
        )

    return app


app = create_app()
