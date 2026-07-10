"""RAG store — grounding context for the HORUS brain (master plan Part 4.1/4.2).

Retrieval-augmented grounding over the MITRE ATT&CK corpus (defensive framing) and the
geo-threat taxonomy. Two interchangeable backends behind one interface:

* ``KeywordRetriever`` — a deterministic, dependency-free TF-IDF-style retriever. This is
  the default so RAG works out of the box and in tests (reproducible, no model download).
* ``ChromaRetriever`` — vector search via ChromaDB when it's installed and configured.

The rest of the system depends only on ``RagStore``, so swapping backends changes nothing
upstream. On the GPU box, set the Chroma backend for semantic recall; the MVP path stays
identical in shape.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Protocol

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass
class RagDocument:
    """A single grounding document."""

    id: str
    text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class RagHit:
    """A retrieved document with its relevance score."""

    document: RagDocument
    score: float


class Retriever(Protocol):
    def add(self, docs: list[RagDocument]) -> None: ...
    def query(self, text: str, k: int) -> list[RagHit]: ...


class KeywordRetriever:
    """Deterministic TF-IDF cosine retriever — no external dependencies."""

    def __init__(self) -> None:
        self._docs: list[RagDocument] = []
        self._tf: list[Counter[str]] = []
        self._df: Counter[str] = Counter()

    def add(self, docs: list[RagDocument]) -> None:
        for doc in docs:
            tokens = _tokenize(f"{doc.text} {' '.join(doc.metadata.values())}")
            tf = Counter(tokens)
            self._docs.append(doc)
            self._tf.append(tf)
            for term in set(tokens):
                self._df[term] += 1

    def _idf(self, term: str) -> float:
        n = len(self._docs)
        return math.log((n + 1) / (self._df.get(term, 0) + 1)) + 1.0

    def query(self, text: str, k: int) -> list[RagHit]:
        if not self._docs:
            return []
        q_tokens = _tokenize(text)
        q_tf = Counter(q_tokens)
        q_vec = {t: q_tf[t] * self._idf(t) for t in q_tf}
        q_norm = math.sqrt(sum(v * v for v in q_vec.values())) or 1.0

        hits: list[RagHit] = []
        for doc, tf in zip(self._docs, self._tf, strict=True):
            d_vec = {t: c * self._idf(t) for t, c in tf.items()}
            d_norm = math.sqrt(sum(v * v for v in d_vec.values())) or 1.0
            dot = sum(q_vec.get(t, 0.0) * d_vec.get(t, 0.0) for t in q_vec)
            score = dot / (q_norm * d_norm)
            if score > 0:
                hits.append(RagHit(document=doc, score=round(score, 4)))
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:k]


class RagStore:
    """Facade over a retriever backend. Use ``RagStore.default()`` to construct."""

    def __init__(self, retriever: Retriever) -> None:
        self.retriever = retriever

    def add(self, docs: list[RagDocument]) -> None:
        self.retriever.add(docs)

    def query(self, text: str, k: int | None = None) -> list[RagHit]:
        from core.config import settings

        return self.retriever.query(text, k or settings.rag_top_k)

    def context_block(self, text: str, k: int | None = None) -> str:
        """Retrieved docs formatted as a grounding block for the model prompt."""
        hits = self.query(text, k)
        lines = []
        for h in hits:
            tag = h.document.metadata.get("id", h.document.id)
            name = h.document.metadata.get("name", "")
            lines.append(f"[{tag}] {name}: {h.document.text}")
        return "\n".join(lines)

    @classmethod
    def default(cls) -> RagStore:
        """Keyword retriever by default; Chroma only when explicitly opted in (RAG_BACKEND).

        Keeping keyword as the default makes retrieval deterministic and dependency-free
        everywhere (tests, CI, laptop). The full stack sets ``RAG_BACKEND=chroma`` for
        semantic recall; if Chroma can't initialize it falls back gracefully.
        """
        from core.config import settings

        if settings.rag_backend.lower() == "chroma":
            try:
                from rag.chroma_backend import build_chroma_retriever

                retriever = build_chroma_retriever()
                if retriever is not None:
                    return cls(retriever)
            except Exception:  # any Chroma issue -> deterministic fallback
                pass
        return cls(KeywordRetriever())
