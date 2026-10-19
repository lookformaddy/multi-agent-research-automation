"""Small deterministic text helpers shared by retrieval and the critic.

Everything here is pure and order-stable so that runs are reproducible:
the same question over the same corpora always yields the same report.
"""

from __future__ import annotations

import re

STOPWORDS = frozenset(
    """
    the a an and or of to in for on with without is are was were be been being
    how can we do does did what why when which who whom this that these those
    it its as at by from into over under more most other others than then so
    such no not only also should would could there here their they them our
    your you i me my we us he she his her had has have having if but about
    between across per via one two three first second
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def tokenize(text: str) -> list[str]:
    """Lowercase content tokens (stopwords and very short tokens removed)."""
    return [
        tok
        for tok in _TOKEN_RE.findall(text.lower())
        if len(tok) > 2 and tok not in STOPWORDS
    ]


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.split(text.strip()) if s.strip()]


def best_sentence(text: str, query_terms: list[str]) -> str:
    """Return the sentence with the highest query-term overlap.

    Ties break toward the earlier sentence, keeping selection deterministic.
    """
    sentences = split_sentences(text)
    if not sentences:
        return text.strip()
    wanted = set(query_terms)
    best, best_score = sentences[0], -1
    for sentence in sentences:
        score = len(wanted & set(tokenize(sentence)))
        if score > best_score:
            best, best_score = sentence, score
    return best
