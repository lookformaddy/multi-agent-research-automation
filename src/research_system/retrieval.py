"""Deterministic lexical retrieval over a corpus.

Scoring is a transparent weighted term overlap: title matches weigh most,
then tags, then body. Ties break by source id so result order is stable
across runs and machines. This deliberately avoids embeddings so the whole
pipeline runs offline with zero external services; the interface is small
enough to swap in a vector index later (see docs/architecture.md).
"""

from __future__ import annotations

from collections import Counter

from .models import Passage, SourceDocument
from .text import best_sentence, tokenize

TITLE_WEIGHT = 3.0
TAG_WEIGHT = 2.0
BODY_WEIGHT = 1.0


def score_document(query_terms: list[str], doc: SourceDocument) -> float:
    title_counts = Counter(tokenize(doc.title))
    tag_counts = Counter(tokenize(" ".join(doc.tags)))
    body_counts = Counter(tokenize(doc.body))
    score = 0.0
    for term in set(query_terms):
        score += TITLE_WEIGHT * title_counts.get(term, 0)
        score += TAG_WEIGHT * tag_counts.get(term, 0)
        score += BODY_WEIGHT * body_counts.get(term, 0)
    return score


def search_documents(
    query: str, documents: list[SourceDocument], top_k: int = 3
) -> list[Passage]:
    """Rank documents for ``query`` and return cited excerpt passages."""
    query_terms = tokenize(query)
    if not query_terms:
        return []
    scored: list[tuple[float, SourceDocument]] = []
    for doc in documents:
        score = score_document(query_terms, doc)
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda item: (-item[0], item[1].id))
    passages: list[Passage] = []
    for score, doc in scored[:top_k]:
        passages.append(
            Passage(
                source_id=doc.id,
                source_title=doc.title,
                kind=doc.kind,
                excerpt=best_sentence(doc.body, query_terms),
                score=round(score, 3),
            )
        )
    return passages
