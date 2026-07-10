"""Base collection agent — the shared contract every ARGUS "eye" implements.

An agent owns a set of passive tools, runs the ones the RoE enables (concurrently),
aggregates their normalized findings, persists them to the Knowledge Plane, and returns
a lightweight typed result. Agents never pass big blobs to each other — only references
and counts (master plan Part 2.1).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import structlog

from core.findings_store import persist_findings
from schemas.auth import AuthContext, AuthorizationError
from schemas.findings import Finding, ToolResult
from schemas.subject import Subject
from tools.base import IntelTool

log = structlog.get_logger("horus.agent")


@dataclass
class AgentResult:
    """What an agent reports back: counts + entity keys, not data blobs."""

    agent: str
    findings_count: int = 0
    persisted: int = 0
    entity_keys: list[str] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BaseAgent:
    """Runs a set of IntelTools for a subject, honoring the RoE, and persists findings."""

    name: str = "agent"

    def __init__(self, tools: list[IntelTool]) -> None:
        self.tools = tools

    def _enabled_tools(self, ctx: AuthContext) -> list[IntelTool]:
        """Only tools whose source category the RoE enables get to run."""
        return [t for t in self.tools if ctx.roe.allows_source(t.source_category)]

    async def collect(self, subject: Subject, ctx: AuthContext) -> AgentResult:
        """Run the enabled tools concurrently, persist findings, return a summary."""
        tools = self._enabled_tools(ctx)
        result = AgentResult(agent=self.name)
        if not tools:
            log.info("agent_no_enabled_tools", agent=self.name, subject=subject.value)
            return result

        outcomes = await asyncio.gather(
            *(self._run_tool(t, subject, ctx) for t in tools), return_exceptions=True
        )

        all_findings: list[Finding] = []
        for tool, outcome in zip(tools, outcomes, strict=True):
            if isinstance(outcome, AuthorizationError):
                result.errors.append(f"{tool.name}: refused ({outcome})")
                continue
            if isinstance(outcome, Exception):
                result.errors.append(f"{tool.name}: {outcome}")
                continue
            result.tool_results.append(outcome)
            if outcome.error:
                result.errors.append(f"{tool.name}: {outcome.error}")
            all_findings.extend(outcome.findings)

        # Let subclasses derive extra findings from what the tools returned.
        all_findings.extend(self.post_process(subject, ctx, all_findings))

        result.findings_count = len(all_findings)
        result.entity_keys = [f.node_key() for f in all_findings]
        result.persisted = await persist_findings(ctx.job_id, all_findings)
        log.info(
            "agent_collected",
            agent=self.name,
            subject=subject.value,
            findings=result.findings_count,
            persisted=result.persisted,
            errors=len(result.errors),
        )
        return result

    async def _run_tool(self, tool: IntelTool, subject: Subject, ctx: AuthContext) -> ToolResult:
        return await tool(subject, ctx)

    def post_process(
        self, subject: Subject, ctx: AuthContext, findings: list[Finding]
    ) -> list[Finding]:
        """Hook for agent-specific derivations (e.g. email patterns). Default: nothing."""
        return []
