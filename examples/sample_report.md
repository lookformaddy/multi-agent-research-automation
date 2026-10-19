# Research Report: How can we reduce cloud infrastructure costs without hurting reliability?

*Job `job-demo-0001` · Generated 2026-10-19T01:06:36.358100+00:00*

## Executive Summary

This report answers the question: “How can we reduce cloud infrastructure costs without hurting reliability?” It is based on 10 evidence-backed claims drawn from 6 sources across documents, tickets and metrics. Key findings: Rightsizing is the single highest-yield lever for reducing cloud infrastructure costs in most estates. An error budget converts a reliability target into an explicit allowance for failure over a rolling window. Total spend grew 22 percent year over year while provisioned compute capacity grew 31 percent, which means unit efficiency declined even as the bill rose.

## Background and Current State

- Rightsizing is the single highest-yield lever for reducing cloud infrastructure costs in most estates. [1]
- An error budget converts a reliability target into an explicit allowance for failure over a rolling window. [2]

## Evidence and Metrics

- Total spend grew 22 percent year over year while provisioned compute capacity grew 31 percent, which means unit efficiency declined even as the bill rose. [3]
- Password and account access issues made up 27 percent of volume, billing questions 18 percent, and order status 12 percent. [4]

## Operational Signals

- A storage audit found dozens of unattached volumes left behind by terminated instances, some older than a year. [5]
- When a service burns its budget early, the team freezes risky changes and shifts effort to reliability work until the budget recovers. [2]

## Risks and Trade-offs

- Error budgets give cost and reliability conversations a shared language because every change can be priced in budget terms. [2]
- The reliability team requested a freeze on non-essential changes until the budget recovers. [6]

## Recommended Actions

- Teams that ignore error budgets tend to over-invest in marginal availability that customers never notice. [2]
- Compute spend concentrated in three services that together represent almost half of the compute total. [3]

## Verification & Confidence

- Claims checked: **10**
- Verified against sources: **10**
- Flagged as unsupported: **0**
- Overall confidence: **100%** (verified / total)

Method: Each claim is checked against the full text of its cited sources: citations must resolve, and at least the configured fraction of the claim's content terms must appear in the cited sources.

## Sources

1. **Rightsizing Idle Compute: A Practical Guide** (`doc-cloud-rightsizing`, doc)
2. **Error Budgets: Balancing Reliability and Change** (`doc-reliability-error-budgets`, doc)
3. **Cloud spend by category, trailing twelve months** (`metric-cloud-spend-breakdown`, metric)
4. **Support ticket volume by category, last quarter** (`metric-support-volume`, metric)
5. **Orphaned storage volumes found during audit** (`ticket-orphaned-volumes`, ticket)
6. **Change freeze requested after error budget exhaustion** (`ticket-reliability-freeze`, ticket)

## Claim Audit Trail

| Claim | Support | Verified | Flags |
|---|---|---|---|
| claim-01 | 1.00 | yes | — |
| claim-02 | 1.00 | yes | — |
| claim-03 | 1.00 | yes | — |
| claim-04 | 1.00 | yes | — |
| claim-05 | 1.00 | yes | — |
| claim-06 | 1.00 | yes | — |
| claim-07 | 1.00 | yes | — |
| claim-08 | 1.00 | yes | — |
| claim-09 | 1.00 | yes | — |
| claim-10 | 1.00 | yes | — |

