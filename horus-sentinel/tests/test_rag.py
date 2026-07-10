"""RAG store tests — deterministic keyword retrieval over the ATT&CK corpus."""

from rag.loader import get_technique_index, load_attack_documents
from rag.store import KeywordRetriever, RagDocument, RagStore


def _store() -> RagStore:
    store = RagStore(KeywordRetriever())
    store.add(load_attack_documents())
    return store


def test_attack_corpus_loads():
    docs = load_attack_documents()
    ids = {d.id for d in docs}
    assert "T1590" in ids  # Gather Victim Network Information
    assert "T1596" in ids  # Search Open Technical Databases


def test_dns_query_retrieves_network_recon_technique():
    store = _store()
    hits = store.query("DNS WHOIS subdomains certificate transparency", k=3)
    top_ids = [h.document.metadata["id"] for h in hits]
    assert any(tid in ("T1590", "T1596") for tid in top_ids)


def test_version_query_retrieves_host_info_technique():
    store = _store()
    hits = store.query("web server software version header fingerprint", k=2)
    assert hits
    assert hits[0].score > 0


def test_technique_index_has_defensive_notes():
    index = get_technique_index()
    assert "T1592" in index
    assert index["T1592"]["defensive_note"]


def test_context_block_is_formatted():
    store = _store()
    block = store.context_block("identity email phishing", k=2)
    assert "[" in block and "]" in block


def test_empty_store_returns_no_hits():
    store = RagStore(KeywordRetriever())
    assert store.query("anything", k=5) == []
    store.add([RagDocument(id="X", text="hello world", metadata={"id": "X"})])
    assert len(store.query("hello", k=5)) == 1
