# Architecture

## Overview

The system is a small, explicit multi-agent pipeline. One orchestrator owns
control flow; five agents own cognition-shaped steps; a blackboard owns all
shared state. Nothing is hidden in prompts or globals, which is what makes
runs auditable and testable end to end.

```
question ──► Orchestrator ──► Planner ──► Researcher ──► Analyst
                  │                                            │
                  │                                            ▼
                  └──── trace ◄──── Writer ◄──── Critic ◄── claims
                                    │
                                    ▼
                        Report (JSON + Markdown)
```

## The state machine

The orchestrator's transition table is declared in
`orchestrator.StateMachine.TRANSITIONS` and enforced at runtime — an agent
cannot be reached out of order:

| From | To |
|---|---|
| idle | planning, failed |
| planning | researching, failed |
| researching | analyzing, failed |
| analyzing | reviewing, failed |
| reviewing | writing, failed |
| writing | completed, failed |

State order encodes a deliberate design choice: the **critic runs before
the writer**, so the writer renders verification results (flags, support
scores) instead of the report being annotated after the fact.

## Agents and their tools

Tool access is per-agent and explicit (`AgentContext`):

| Agent | Tools | Reads | Writes |
|---|---|---|---|
| Planner | — | question | plan (5 aspect subtasks) |
| Researcher | `connectors.search` | plan | findings |
| Analyst | blackboard read/write | findings | claims |
| Critic | `connectors.lookup` | claims | verified/flagged claims, verification summary |
| Writer | blackboard read/write | claims, verification | sections, executive summary |

Agents never call each other. All communication goes through the
blackboard, so any agent can be retried, replaced (e.g. an LLM-backed
planner), or unit-tested in isolation.

## Blackboard contract

Keys: `question`, `plan`, `findings`, `claims`, `sections`, `notes`, plus
`verification_summary` and `executive_summary` slots filled by the critic
and writer. `Blackboard.snapshot()` produces the compact state summary used
in tests and debugging.

## Retrieval

`retrieval.search_documents` ranks with weighted term overlap
(title ×3, tags ×2, body ×1) and deterministic tie-breaking by source id.
Passages carry the best-matching sentence as an excerpt plus the source id —
the citation is created at retrieval time and can never be detached from
the text it supports.

## Verification model

The critic scores each claim as:

```
support = |content terms of claim ∩ content terms of cited sources|
          ─────────────────────────────────────────────────────────
                        |content terms of claim|
```

A claim is **verified** when all citations resolve and
`support ≥ min_claim_support` (default 0.5). Because analyst claims are
extractive (verbatim source sentences), honest claims score 1.0; the
threshold exists to catch claims whose wording drifts from their evidence
— exactly the failure mode the fabricated-claim test exercises.

Report confidence = verified / total claims, surfaced in both JSON and
Markdown outputs.

## Budgets and retries

- **Step budget** (`max_steps`, default 60): each agent attempt costs 1
  step; each subtask search costs 1 step. Exhaustion raises
  `BudgetExceeded` and the run lands in `failed` with the reason recorded.
- **Retries** (`max_retries`, default 2): any agent exception is retried;
  the trace records every attempt. Exhaustion fails the run with the
  agent's error attached.

## Determinism

No randomness, no wall-clock dependence in the pipeline (timestamps are
injected), stable sort orders everywhere. `test_run_is_deterministic`
asserts two runs produce identical report models.

## Production hardening (not in this demo)

- Replace the in-memory job dict with a database and run jobs on a queue
  (the API already isolates execution behind `Orchestrator.run`).
- Put connectors behind per-tenant configuration with credentials from a
  secret store; add connector-level caching and timeouts.
- Swap lexical retrieval for hybrid BM25 + embeddings behind the same
  `search_documents` interface; add an entailment model to the critic.
- Ship traces to your observability stack (they are already structured
  pydantic events) and alert on confidence dropping below a floor.
