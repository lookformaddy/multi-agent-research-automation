from research_system.connectors import ConnectorRegistry, DocsConnector
from research_system.retrieval import score_document, search_documents
from research_system.text import tokenize


def test_tokenize_removes_stopwords():
    terms = tokenize("How can we reduce the cloud costs?")
    assert "cloud" in terms and "reduce" in terms
    assert "how" not in terms and "the" not in terms


def test_registry_loads_all_corpora():
    registry = ConnectorRegistry()
    kinds = {c.name for c in registry.connectors}
    assert kinds == {"docs", "tickets", "metrics"}
    assert len(registry.all_documents()) == 20
    assert all(len(c) > 0 for c in registry.connectors)


def test_search_ranks_relevant_doc_first():
    connector = DocsConnector()
    passages = connector.search("reduce cloud infrastructure costs rightsizing", top_k=3)
    assert passages
    assert passages[0].source_id == "doc-cloud-rightsizing"
    assert passages[0].score > 0


def test_search_is_deterministic():
    registry = ConnectorRegistry()
    first = registry.search_all("supplier lead time variability", top_k=3)
    second = registry.search_all("supplier lead time variability", top_k=3)
    assert [p.source_id for p in first] == [p.source_id for p in second]


def test_search_returns_cited_excerpts():
    registry = ConnectorRegistry()
    passages = registry.search_all("password reset ticket volume", top_k=2)
    assert passages
    for passage in passages:
        assert passage.excerpt
        doc = registry.get(passage.source_id)
        assert doc is not None
        assert passage.excerpt in doc.body


def test_score_zero_for_unrelated_query():
    registry = ConnectorRegistry()
    doc = registry.get("doc-churn-signals")
    assert score_document(tokenize("quantum entanglement photon"), doc) == 0.0


def test_lookup_unknown_source_returns_none():
    assert ConnectorRegistry().get("does-not-exist") is None
