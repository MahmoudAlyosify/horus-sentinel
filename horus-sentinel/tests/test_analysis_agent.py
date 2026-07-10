"""Analysis agent tests — grounded prioritized findings + bounded adjustment (offline brain)."""

import httpx
import pytest
import respx

from agents.analysis_agent import analysis_agent
from core.db import init_db
from core.findings_store import persist_findings
from horus_brain.horus_provider import horus_provider
from schemas.findings import EntityKind, Finding


def _f(kind, value, *, related_to=None, rel=None, attrs=None):
    return Finding(
        entity_kind=kind,
        entity_value=value,
        attributes=attrs or {},
        related_to=related_to,
        relationship=rel,
        produced_by="test",
    )


async def _seed(job: str):
    init_db()
    await persist_findings(
        job,
        [
            _f(EntityKind.DOMAIN, "example.com"),
            _f(EntityKind.IP, "93.184.216.34", related_to="example.com", rel="RESOLVES_TO"),
            _f(
                EntityKind.SUBDOMAIN,
                "api.example.com",
                related_to="example.com",
                rel="HAS_SUBDOMAIN",
            ),
            _f(
                EntityKind.SERVICE,
                "example.com:443",
                related_to="93.184.216.34",
                rel="EXPOSES",
                attrs={"internet_facing": True},
            ),
            _f(EntityKind.TECHNOLOGY, "nginx", related_to="example.com:443", rel="RUNS"),
            _f(
                EntityKind.CVE,
                "CVE-2021-23017",
                related_to="nginx",
                rel="HAS_VULNERABILITY",
                attrs={"cvss": 9.8, "summary": "nginx resolver overflow"},
            ),
        ],
    )


@pytest.fixture(autouse=True)
def _no_ollama():
    """Force the offline path by refusing the Ollama endpoint."""
    with respx.mock(assert_all_called=False) as router:
        router.post(horus_provider.endpoint).mock(side_effect=httpx.ConnectError("refused"))
        yield router


async def test_analysis_produces_grounded_report_card():
    await _seed("anajob1")
    card, graph = await analysis_agent.analyze("anajob1", "example.com")

    assert card.subject == "example.com"
    assert card.generated_by == "offline-synthesis"
    assert card.entity_count == graph["nodes"].__len__()
    assert card.prioritized_findings, "expected at least one prioritized finding"
    # Every prioritized finding is framework-mapped and evidence-aware.
    top = card.prioritized_findings[0]
    assert top.framework is not None
    assert top.recommendation


async def test_critical_cve_triggers_bounded_adjustment():
    await _seed("anajob2")
    card, _ = await analysis_agent.analyze("anajob2", "example.com")
    assert card.critical_cve_hits == 1
    assert card.band_adjustments, "critical CVE should trigger a logged ±1 adjustment"
    adj = card.band_adjustments[0]
    assert adj.delta == 1
    assert adj.from_band != adj.to_band


async def test_cve_finding_is_high_priority():
    await _seed("anajob3")
    card, _ = await analysis_agent.analyze("anajob3", "example.com")
    keys = [p.entity_key for p in card.prioritized_findings]
    assert any(k.startswith("CVE:") for k in keys)
