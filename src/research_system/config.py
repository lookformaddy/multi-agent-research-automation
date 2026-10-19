"""Runtime configuration for the orchestrator and its agents."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OrchestratorConfig(BaseModel):
    """Budgets and thresholds that keep agent runs bounded and auditable."""

    max_steps: int = Field(default=60, ge=1, description="Total step budget per run.")
    max_retries: int = Field(
        default=2, ge=0, description="Retries per agent after a failure."
    )
    top_k: int = Field(default=3, ge=1, le=10, description="Passages per subtask.")
    min_claim_support: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum fraction of a claim's content terms that must appear "
        "in its cited sources for the critic to mark it verified.",
    )
    max_claims_per_finding: int = Field(default=2, ge=1, le=5)
