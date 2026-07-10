"""Optional ChromaDB retriever backend (master plan Part 7 — Vector DB).

Lazily constructed: if ``chromadb`` is not installed the factory returns ``None`` and the
store falls back to the keyword retriever. On the full stack, this gives semantic recall
over the same documents with a persistent collection.
"""

from __future__ import annotations

import structlog

from rag.store import RagDocument, RagHit

log = structlog.get_logger("horus.rag.chroma")

_COLLECTION = "horus_grounding"


def build_chroma_retriever():  # noqa: ANN201 (returns a duck-typed Retriever or None)
    """Return a Chroma-backed retriever, or ``None`` if Chroma is unavailable."""
    try:
        import chromadb
    except ImportError:
        return None

    from core.config import settings

    try:
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collection = client.get_or_create_collection(_COLLECTION)
    except Exception as exc:
        log.warning("chroma_init_failed", error=str(exc))
        return None

    return _ChromaRetriever(collection)


class _ChromaRetriever:
    """Adapts a Chroma collection to the Retriever protocol."""

    def __init__(self, collection) -> None:  # noqa: ANN001
        self._c = collection

    def add(self, docs: list[RagDocument]) -> None:
        if not docs:
            return
        self._c.upsert(
            ids=[d.id for d in docs],
            documents=[d.text for d in docs],
            metadatas=[d.metadata or {"_": "_"} for d in docs],
        )

    def query(self, text: str, k: int) -> list[RagHit]:
        res = self._c.query(query_texts=[text], n_results=k)
        hits: list[RagHit] = []
        ids = res.get("ids", [[]])[0]
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0] or [0.0] * len(ids)
        for i, doc_id in enumerate(ids):
            hits.append(
                RagHit(
                    document=RagDocument(id=doc_id, text=docs[i], metadata=metas[i] or {}),
                    score=round(1.0 - float(dists[i]), 4),
                )
            )
        return hits
