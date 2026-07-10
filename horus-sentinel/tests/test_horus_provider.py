"""HORUS provider tests — offline fallback + section parsing (no Ollama needed)."""

import httpx
import respx

from horus_brain.horus_provider import (
    HorusReasoningProvider,
    ReasoningInput,
    _split_sections,
)


def _input() -> ReasoningInput:
    return ReasoningInput(
        subject="example.com",
        subgraph={"root": "Domain:example.com", "nodes": [], "edges": []},
        rag_context="[T1590] Gather Victim Network Information: DNS exposure.",
        entity_count=7,
        top_band="High",
        critical_cve_hits=1,
        facts=[
            "Entity mix: 3 Subdomain, 1 IP",
            "Dominant modalities in Sinai:2018: ied (instability 0.78)",
        ],
    )


async def test_offline_fallback_when_ollama_unreachable():
    prov = HorusReasoningProvider()
    with respx.mock(assert_all_called=False) as router:
        router.post(prov.endpoint).mock(side_effect=httpx.ConnectError("refused"))
        card = await prov.reason(_input())
    assert card.generated_by == "offline-synthesis"
    assert "example.com" in card.executive_summary
    assert card.entity_count == 7
    assert card.top_band == "High"
    # Grounded geo fact surfaces in the geopolitical section.
    assert "instability" in card.geopolitical_context.lower()


async def test_uses_model_output_when_available():
    prov = HorusReasoningProvider()
    model_text = (
        "EXECUTIVE SUMMARY:\nHigh exposure observed.\n"
        "GEOPOLITICAL CONTEXT:\nElevated regional instability.\n"
        "THREAT ASSESSMENT:\nMultiple public services.\n"
        "CONCLUSION:\nValidate before final.\n"
    )
    with respx.mock(assert_all_called=False) as router:
        router.post(prov.endpoint).mock(
            return_value=httpx.Response(200, json={"response": model_text})
        )
        card = await prov.reason(_input())
    assert card.generated_by == prov.model
    assert "High exposure observed" in card.executive_summary
    assert "instability" in card.geopolitical_context.lower()
    assert "Validate before final" in card.conclusion


def test_section_splitter_handles_headers():
    raw = "EXECUTIVE SUMMARY: one\nGEOPOLITICAL CONTEXT: two\nTHREAT ASSESSMENT: three\nCONCLUSION: four"
    sections = _split_sections(raw)
    assert sections["executive_summary"] == "one"
    assert sections["conclusion"] == "four"


def test_section_splitter_falls_back_to_summary():
    sections = _split_sections("just some unstructured text")
    assert sections["executive_summary"] == "just some unstructured text"
