"""Load grounding corpora into a RagStore (master plan Part 4.1).

Seeds the store with the curated MITRE ATT&CK techniques (TA0043 Reconnaissance /
TA0042 Resource Development, defensive framing) plus the geo-threat taxonomy. On the full
stack the same loader can ingest the complete ATT&CK export and the full geo corpus.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import structlog

from rag.store import RagDocument, RagStore

log = structlog.get_logger("horus.rag.loader")

_ATTACK = Path(__file__).resolve().parent.parent / "data" / "attack_knowledge.json"


def load_attack_documents() -> list[RagDocument]:
    """Read the ATT&CK + geo-taxonomy knowledge file into RagDocuments."""
    if not _ATTACK.exists():
        log.warning("attack_knowledge_missing", path=str(_ATTACK))
        return []
    data = json.loads(_ATTACK.read_text(encoding="utf-8"))
    docs: list[RagDocument] = []
    for t in data.get("techniques", []):
        docs.append(
            RagDocument(
                id=t["id"],
                text=f"{t['text']} Defensive note: {t.get('defensive_note', '')}",
                metadata={
                    "id": t["id"],
                    "name": t["name"],
                    "tactic": t.get("tactic", ""),
                    "tactic_name": t.get("tactic_name", ""),
                    "kind": "attack_technique",
                },
            )
        )
    for g in data.get("geo_taxonomy", []):
        docs.append(
            RagDocument(
                id=g["id"],
                text=g["text"],
                metadata={"id": g["id"], "name": g["name"], "kind": "geo_taxonomy"},
            )
        )
    return docs


@lru_cache(maxsize=1)
def get_technique_index() -> dict[str, dict[str, str]]:
    """id -> {name, tactic, tactic_name, defensive_note} for recommendation lookup."""
    if not _ATTACK.exists():
        return {}
    data = json.loads(_ATTACK.read_text(encoding="utf-8"))
    index: dict[str, dict[str, str]] = {}
    for t in data.get("techniques", []):
        index[t["id"]] = {
            "name": t["name"],
            "tactic": t.get("tactic", ""),
            "tactic_name": t.get("tactic_name", ""),
            "defensive_note": t.get("defensive_note", ""),
        }
    for g in data.get("geo_taxonomy", []):
        index[g["id"]] = {
            "name": g["name"],
            "tactic": "",
            "tactic_name": "Geopolitical",
            "defensive_note": g.get("text", ""),
        }
    return index


@lru_cache(maxsize=1)
def get_grounding_store() -> RagStore:
    """Build (once) the process-wide grounding store, seeded with ATT&CK + geo taxonomy."""
    store = RagStore.default()
    docs = load_attack_documents()
    store.add(docs)
    log.info("rag_seeded", documents=len(docs), backend=type(store.retriever).__name__)
    return store
