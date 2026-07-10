"""Threat-Intelligence Enrichment Agent — reputation + known-CVE context.

Master plan Part 3.4. Unlike the collection agents, this one enriches entities *already
discovered* by the swarm: it reads IPs and technologies from the Knowledge Plane and
attaches reputation (AbuseIPDB) and known-vulnerability (OSV) context. This is the graph-
as-source-of-truth pattern — the agent reasons over what the eyes already saw.
"""

from __future__ import annotations

import asyncio

import structlog

from agents.base import AgentResult, BaseAgent
from core.findings_store import load_findings, persist_findings
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Finding
from schemas.roe import SourceCategory
from schemas.subject import Subject, SubjectType
from tools.osv_tool import OsvTool
from tools.reputation_tool import ReputationTool

log = structlog.get_logger("horus.agent.threat_intel")


class ThreatIntelAgent(BaseAgent):
    """Enrich discovered IPs (reputation) and technologies (known CVEs)."""

    name = "threat_intel"

    def __init__(self) -> None:
        super().__init__(tools=[ReputationTool(), OsvTool()])
        self._reputation = ReputationTool()
        self._osv = OsvTool()

    async def collect(self, subject: Subject, ctx: AuthContext) -> AgentResult:
        result = AgentResult(agent=self.name)
        if not ctx.roe.allows_source(SourceCategory.THREAT_INTEL):
            log.info("threat_intel_not_enabled", job_id=ctx.job_id)
            return result

        prior = load_findings(ctx.job_id)
        ips = sorted({f.entity_value for f in prior if f.entity_kind == EntityKind.IP})
        techs = [f for f in prior if f.entity_kind == EntityKind.TECHNOLOGY]

        tasks = []
        for ip in ips:
            tasks.append(self._enrich_ip(ip, ctx, result))
        for tech in techs:
            tasks.append(self._enrich_tech(tech, ctx, result))

        collected: list[list[Finding]] = await asyncio.gather(*tasks) if tasks else []
        all_findings = [f for group in collected for f in group]

        result.findings_count = len(all_findings)
        result.entity_keys = [f.node_key() for f in all_findings]
        result.persisted = await persist_findings(ctx.job_id, all_findings)
        log.info(
            "threat_intel_collected",
            job_id=ctx.job_id,
            ips=len(ips),
            techs=len(techs),
            findings=result.findings_count,
        )
        return result

    async def _enrich_ip(self, ip: str, ctx: AuthContext, result: AgentResult) -> list[Finding]:
        subj = Subject(type=SubjectType.ENTITY, value=ip)
        res = await self._reputation(subj, ctx)
        result.tool_results.append(res)
        if res.error:
            result.errors.append(f"reputation[{ip}]: {res.error}")
        return res.findings

    async def _enrich_tech(
        self, tech: Finding, ctx: AuthContext, result: AgentResult
    ) -> list[Finding]:
        ecosystem = tech.attributes.get("ecosystem")
        version = tech.attributes.get("version")
        name = tech.entity_value
        value = f"{ecosystem}:{name}:{version}" if ecosystem and version else name
        subj = Subject(type=SubjectType.ENTITY, value=value)
        res = await self._osv(subj, ctx)
        result.tool_results.append(res)
        if res.error:
            result.errors.append(f"osv[{name}]: {res.error}")
        return res.findings
