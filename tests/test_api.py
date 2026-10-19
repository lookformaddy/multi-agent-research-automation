from fastapi.testclient import TestClient

from research_system.api import create_app
from research_system.report import render_markdown

DEMO_QUESTION = "How can we reduce cloud infrastructure costs without hurting reliability?"

client = TestClient(create_app())


def test_health_and_sources():
    assert client.get("/health").json()["status"] == "ok"
    sources = client.get("/sources").json()
    assert len(sources) == 20
    assert {s["kind"] for s in sources} == {"doc", "ticket", "metric"}


def test_submit_job_and_fetch_report():
    response = client.post("/jobs", json={"question": DEMO_QUESTION})
    assert response.status_code == 201
    job = response.json()
    assert job["status"] == "completed"
    job_id = job["id"]

    fetched = client.get(f"/jobs/{job_id}")
    assert fetched.status_code == 200
    assert fetched.json()["report"]["verification"]["total_claims"] > 0

    md = client.get(f"/jobs/{job_id}/report", params={"format": "md"})
    assert md.status_code == 200
    assert md.text.startswith("# Research Report:")
    assert "## Verification & Confidence" in md.text
    assert "## Sources" in md.text

    trace = client.get(f"/jobs/{job_id}/trace")
    assert trace.status_code == 200
    assert "planning" in trace.text


def test_job_validation_and_404s():
    assert client.post("/jobs", json={"question": "short"}).status_code == 422
    assert client.get("/jobs/job-9999").status_code == 404
    assert client.get("/jobs/job-9999/report").status_code == 404


def test_failed_job_has_no_report():
    # max_steps=1 guarantees a budget failure inside the first agent.
    response = client.post(
        "/jobs", json={"question": DEMO_QUESTION, "max_steps": 1}
    )
    job = response.json()
    assert job["status"] == "failed"
    assert "budget" in job["error"]
    report = client.get(f"/jobs/{job['id']}/report")
    assert report.status_code == 409


def test_render_markdown_structure(report):
    md = render_markdown(report)
    assert "## Executive Summary" in md
    assert "## Claim Audit Trail" in md
    for source in report.sources:
        assert source.title in md
