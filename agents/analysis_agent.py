"""
Analysis Agent (LLM + RAG) — provider-abstracted, safe fallback to mock mode.

This agent consumes a `ReconState` and returns an `AnalysisResult`.

Behavior:
- Default mode `mock` returns a short deterministic summary useful for local dev
- If `provider='chroma'` and `chromadb` + `sentence-transformers` are available,
  it will build an in-memory collection, index the agent `kb_refs` as documents,
  and perform a simple retrieval + call to an LLM function (LLM call must be
  provided via `llm_callable`, see below). This keeps the integration pluggable.

Note: For safety and deterministic testing we keep `mock` as the default.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from schemas.recon_state import ReconState
from schemas.analysis import AnalysisResult, Finding


class AnalysisAgent:
    def __init__(
        self,
        provider: str = "mock",
        chroma_client: Optional[object] = None,
        llm_callable: Optional[Callable[[str, List[Dict[str, Any]]], str]] = None,
    ) -> None:
        self.provider = provider
        self.chroma = chroma_client
        self.llm_callable = llm_callable

        # Try to import chromadb embedding helper lazily when needed
        self._chroma_available = False
        if provider == "chroma":
            try:
                import chromadb  # type: ignore

                self._chroma_available = True
            except Exception:
                self._chroma_available = False

    async def run(self, state: ReconState) -> AnalysisResult:
        """Produce an AnalysisResult from a ReconState.

        If in `mock` mode, return a small deterministic summary.
        If in `chroma` mode and available, index text and run retrieval.
        """
        # Collect textual evidence from kb_refs
        docs: List[Dict[str, Any]] = []
        for source, payload in state.kb_refs.items():
            try:
                text = json.dumps(payload, default=str)
            except Exception:
                text = str(payload)
            docs.append({"id": f"{state.job_id}-{source}", "source": source, "text": text})

        # Mock fallback
        if self.provider != "chroma" or not self._chroma_available:
            summary = (
                f"Mock Analysis: found {len(state.discovered_domains)} domains, "
                f"{len(state.discovered_subdomains)} subdomains, and {len(state.discovered_ips)} IPs."
            )
            findings: List[Finding] = [
                Finding(
                    id="mock-1",
                    title="Surface summary",
                    summary=summary,
                    evidence_refs=[d["id"] for d in docs],
                    score=0.2,
                )
            ]
            return AnalysisResult(
                executive_summary=summary, findings=findings, rag_refs={s["id"]: s for s in docs}, overall_score=0.2
            )

        # If running with chroma, perform a simple RAG flow (index+retrieve)
        # This block assumes the caller provided a working `chroma_client` and an `llm_callable`.
        if not self.chroma or not self.llm_callable:
            raise RuntimeError("Chroma provider selected but chroma_client or llm_callable missing")

        # Create or get a collection
        collection_name = f"argus_{state.job_id}"
        try:
            collection = self.chroma.get_collection(name=collection_name)
        except Exception:
            collection = self.chroma.create_collection(name=collection_name)

        # Upsert documents
        docs_to_upsert = [{"id": d["id"], "metadata": {"source": d["source"]}, "documents": d["text"]} for d in docs]
        collection.add(**{"ids": [d["id"] for d in docs_to_upsert], "metadatas": [d["metadata"] for d in docs_to_upsert], "documents": [d["documents"] for d in docs_to_upsert]})

        # Simple retrieval: ask LLM to summarize top-k docs
        retrieved = collection.query(query_texts=["summarize"], n_results=3)
        retrieved_texts: List[Dict[str, Any]] = []
        for r in retrieved["results"][0]["documents"]:
            retrieved_texts.append({"text": r})

        # Call LLM for an executive summary
        prompt = (
            "You are an analysis agent. Given the following evidence documents, produce a concise executive summary and 3 prioritized findings.\n\n"
            + "\n---\n".join([t["text"] for t in retrieved_texts])
        )

        llm_output = self.llm_callable(prompt, retrieved_texts)

        # For simplicity we return LLM blob as a single finding
        findings = [
            Finding(id="rag-1", title="LLM findings", summary=llm_output, evidence_refs=[d["id"] for d in docs], score=0.5)
        ]

        return AnalysisResult(executive_summary=llm_output, findings=findings, rag_refs={d["id"]: d for d in docs}, overall_score=0.5)
