"""Network Reconnaissance Agent — ACTIVE, GATED (master plan v2.0 Part 3.4).

Runs active reconnaissance **only** on authorized, in-scope targets (the Authorization
Engine + Tool Abstraction Layer refuse anything else). It is discovery/enumeration only —
active DNS brute-force, TCP connect port scan + banner fingerprint, and a compliant web
crawl. **Absolute stop line:** no exploitation, no auth attempts, no brute-forcing
credentials, no payloads. If a capability would cross into exploitation, it is not built.

Unlike the passive agents (whose tools run concurrently), this agent runs its tools in a
fixed order and persists after each, so the port scanner can see IPs the active-DNS stage
just discovered.
"""

from __future__ import annotations

import structlog

from agents.base import AgentResult, BaseAgent
from core.findings_store import persist_findings
from schemas.auth import AuthContext, AuthorizationError
from schemas.findings import Finding
from schemas.subject import Subject
from tools.active_dns_tool import ActiveDnsTool
from tools.port_scan_tool import PortScanTool
from tools.web_crawl_tool import WebCrawlTool

log = structlog.get_logger("horus.agent.active_recon")


class ActiveReconAgent(BaseAgent):
    """Gated active reconnaissance: active DNS → port/service scan → compliant crawl."""

    name = "active_recon"

    def __init__(self) -> None:
        # Order matters: active DNS first (discovers hosts/IPs), then the port scan (which
        # reads those IPs), then the crawler.
        super().__init__(tools=[ActiveDnsTool(), PortScanTool(), WebCrawlTool()])

    async def collect(self, subject: Subject, ctx: AuthContext) -> AgentResult:
        """Run the enabled active tools sequentially, persisting after each."""
        tools = self._enabled_tools(ctx)
        result = AgentResult(agent=self.name)
        if not tools:
            log.info("active_recon_no_enabled_tools", subject=subject.value)
            return result

        all_findings: list[Finding] = []
        for tool in tools:
            try:
                outcome = await tool(subject, ctx)
            except AuthorizationError as exc:
                # Refusal is a designed control — record it and stop this tool.
                result.errors.append(f"{tool.name}: refused ({exc})")
                log.info("active_tool_refused", tool=tool.name, subject=subject.value)
                continue
            result.tool_results.append(outcome)
            if outcome.error:
                result.errors.append(f"{tool.name}: {outcome.error}")
            if outcome.findings:
                # Persist immediately so the next tool (e.g. port scan) sees these entities.
                await persist_findings(ctx.job_id, outcome.findings)
                all_findings.extend(outcome.findings)

        result.findings_count = len(all_findings)
        result.entity_keys = [f.node_key() for f in all_findings]
        result.persisted = result.findings_count
        log.info(
            "agent_collected",
            agent=self.name,
            subject=subject.value,
            findings=result.findings_count,
            errors=len(result.errors),
        )
        return result
