"""Pluggable source connectors.

A connector owns one corpus and exposes uniform search. The bundled
connectors load synthetic JSON corpora shipped with the package, so the
system runs fully offline and deterministically. To connect a real source
(document store, ticket system, metrics warehouse), implement
``SourceConnector`` with the same interface — no agent changes required.
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Passage, SourceDocument, SourceKind
from .retrieval import search_documents

_DATA_DIR = Path(__file__).parent / "data"


class SourceConnector:
    """Base class: one named corpus + ranked, cited search."""

    name: str = "base"
    kind: SourceKind = SourceKind.DOC

    def __init__(self, documents: list[SourceDocument]):
        self._documents = documents

    def __len__(self) -> int:
        return len(self._documents)

    @property
    def documents(self) -> list[SourceDocument]:
        return list(self._documents)

    def get(self, source_id: str) -> SourceDocument | None:
        for doc in self._documents:
            if doc.id == source_id:
                return doc
        return None

    def search(self, query: str, top_k: int = 3) -> list[Passage]:
        return search_documents(query, self._documents, top_k=top_k)


def _load_corpus(filename: str, kind: SourceKind) -> list[SourceDocument]:
    raw = json.loads((_DATA_DIR / filename).read_text(encoding="utf-8"))
    return [
        SourceDocument(kind=kind, **{k: item[k] for k in ("id", "title", "body", "tags")})
        for item in raw
    ]


class DocsConnector(SourceConnector):
    """Long-form internal documents: guides, reviews, explainers."""

    name = "docs"
    kind = SourceKind.DOC

    def __init__(self):
        super().__init__(_load_corpus("docs.json", SourceKind.DOC))


class TicketsConnector(SourceConnector):
    """Support / operations tickets: incidents, audits, field reports."""

    name = "tickets"
    kind = SourceKind.TICKET

    def __init__(self):
        super().__init__(_load_corpus("tickets.json", SourceKind.TICKET))


class MetricsConnector(SourceConnector):
    """Quantitative snapshots: spend, utilization, volume, cohort metrics."""

    name = "metrics"
    kind = SourceKind.METRIC

    def __init__(self):
        super().__init__(_load_corpus("metrics.json", SourceKind.METRIC))


class ConnectorRegistry:
    """All connectors available to a run, plus unified lookup/search."""

    def __init__(self, connectors: list[SourceConnector] | None = None):
        self._connectors = connectors or [DocsConnector(), TicketsConnector(), MetricsConnector()]

    @property
    def connectors(self) -> list[SourceConnector]:
        return list(self._connectors)

    def all_documents(self) -> list[SourceDocument]:
        docs: list[SourceDocument] = []
        for connector in self._connectors:
            docs.extend(connector.documents)
        return docs

    def get(self, source_id: str) -> SourceDocument | None:
        for connector in self._connectors:
            doc = connector.get(source_id)
            if doc is not None:
                return doc
        return None

    def search_all(self, query: str, top_k: int = 3) -> list[Passage]:
        """Search every connector and merge by score (stable order)."""
        passages: list[Passage] = []
        for connector in self._connectors:
            passages.extend(connector.search(query, top_k=top_k))
        passages.sort(key=lambda p: (-p.score, p.source_id))
        return passages[:top_k]
