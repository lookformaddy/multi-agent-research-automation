from research_system.agents import CriticAgent
from research_system.agents.base import AgentContext
from research_system.blackboard import Blackboard
from research_system.config import OrchestratorConfig
from research_system.connectors import ConnectorRegistry
from research_system.models import Claim
from research_system.trace import RunTrace


def _critic_ctx(claims: list[Claim]) -> AgentContext:
    bb = Blackboard("How can we reduce cloud infrastructure costs?")
    bb.set_claims(claims)
    return AgentContext(
        blackboard=bb,
        config=OrchestratorConfig(min_claim_support=0.5),
        trace=RunTrace(),
        state="reviewing",
        registry=ConnectorRegistry(),
    )


def test_critic_verifies_supported_claim():
    registry = ConnectorRegistry()
    doc = registry.get("doc-cloud-rightsizing")
    claim = Claim(
        id="claim-t1",
        text="Rightsizing is the single highest-yield lever for reducing cloud "
        "infrastructure costs in most estates.",
        source_ids=[doc.id],
    )
    ctx = _critic_ctx([claim])
    summary = CriticAgent().run(ctx)
    assert claim.verified is True
    assert claim.support_score == 1.0
    assert summary.confidence == 1.0


def test_critic_flags_fabricated_claim():
    claim = Claim(
        id="claim-t2",
        text="Quantum teleportation reduced banana imports by ninety percent "
        "according to lunar mining telemetry.",
        source_ids=["doc-cloud-rightsizing"],
    )
    ctx = _critic_ctx([claim])
    summary = CriticAgent().run(ctx)
    assert claim.verified is False
    assert "unsupported_by_sources" in claim.flags
    assert summary.flagged_claim_ids == ["claim-t2"]
    assert summary.confidence == 0.0


def test_critic_flags_missing_and_unresolvable_citations():
    no_cite = Claim(id="claim-t3", text="Anything at all.", source_ids=[])
    bad_cite = Claim(
        id="claim-t4",
        text="Rightsizing reduces cloud infrastructure costs.",
        source_ids=["doc-that-does-not-exist"],
    )
    ctx = _critic_ctx([no_cite, bad_cite])
    summary = CriticAgent().run(ctx)
    assert "no_citation" in no_cite.flags
    assert any(f.startswith("unresolvable_citation") for f in bad_cite.flags)
    assert summary.flagged_claims == 2
