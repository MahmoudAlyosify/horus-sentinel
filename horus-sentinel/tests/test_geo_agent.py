"""Geo-Event agent tests — runs against the bundled sample corpus (no network)."""

from datetime import datetime, timedelta

import pytest

from agents.geo_event_agent import GeoEventAgent
from core.db import init_db
from core.findings_store import load_findings
from schemas.auth import AuthContext
from schemas.findings import EntityKind
from schemas.roe import RoE, SourceCategory
from schemas.subject import Subject, SubjectType


@pytest.fixture(autouse=True)
def _db():
    init_db()


def _ctx(job_id: str) -> AuthContext:
    roe = RoE(
        subject="Sinai",
        enabled_sources=[SourceCategory.GEO_EVENTS],
        signed_by="analyst_test",
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    return AuthContext(job_id=job_id, roe=roe)


async def test_geo_agent_returns_region_context():
    subject = Subject(type=SubjectType.REGION, value="Sinai", year_from=2018, year_to=2019)
    agent = GeoEventAgent()
    result = await agent.collect(subject, _ctx("geojob1"))

    assert result.findings_count > 0
    assert result.persisted == result.findings_count
    kinds = {k.split(":")[0] for k in result.entity_keys}
    assert "Region" in kinds
    assert "Event" in kinds
    assert "ThreatActor" in kinds


async def test_geo_agent_persists_event_attributes():
    subject = Subject(type=SubjectType.REGION, value="Sinai", year_from=2018, year_to=2018)
    agent = GeoEventAgent()
    await agent.collect(subject, _ctx("geojob2"))

    findings = load_findings("geojob2")
    events = [f for f in findings if f.entity_kind == EntityKind.EVENT]
    assert events
    assert "dominant_modalities" in events[0].attributes
    assert events[0].attributes["instability_index"] is not None


async def test_geo_agent_no_records_is_graceful():
    subject = Subject(type=SubjectType.REGION, value="Atlantis", year_from=2018, year_to=2019)
    agent = GeoEventAgent()
    result = await agent.collect(subject, _ctx("geojob3"))
    assert result.findings_count == 0
    assert any("no geo-event records" in e for e in result.errors)
