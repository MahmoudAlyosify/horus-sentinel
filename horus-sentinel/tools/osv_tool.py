"""OSV tool — known-vulnerability correlation over a keyless public API.

Master plan Part 3.4 (informational CVE correlation). OSV.dev is Google's open,
key-free vulnerability database. Given a discovered product + version, it returns known
advisories. This is *informational only* — it never scans; it correlates public data
about software already observed in the graph.
"""

from __future__ import annotations

from typing import Any

from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool

_OSV_QUERY = "https://api.osv.dev/v1/query"


class OsvTool(IntelTool):
    """Correlate a product+version against known vulnerabilities (OSV.dev).

    Reads ``subject`` loosely: the Threat-Intel agent invokes it per discovered technology
    by packing ``{name, version}`` into the subject's ``country_code``-free attributes via
    a synthetic subject. For direct subject use, the subject value is treated as a package.
    """

    name = "osv"
    source_category = SourceCategory.THREAT_INTEL
    cache_ttl = 43200

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        # Subject value form "ecosystem:package:version" or just "package".
        parts = subject.value.split(":")
        query: dict[str, Any]
        if len(parts) == 3:
            ecosystem, package, version = parts
            query = {"package": {"name": package, "ecosystem": ecosystem}, "version": version}
        else:
            query = {"package": {"name": subject.value}}

        data = await get_json_post(_OSV_QUERY, query)
        vulns = (data or {}).get("vulns", []) if isinstance(data, dict) else []
        if not vulns:
            return ToolResult(
                tool=self.name,
                source_category=self.source_category,
                error=f"no known vulnerabilities for '{subject.value}'",
            )

        findings: list[Finding] = []
        evidence: list[Evidence] = []
        for v in vulns[:25]:
            cve_id = v.get("id", "UNKNOWN")
            severity = _max_cvss(v)
            ev = Evidence(
                source=self.name,
                source_category=self.source_category,
                summary=f"{cve_id} affects {subject.value} (cvss={severity})",
                raw_ref=Evidence.digest(v),
            )
            evidence.append(ev)
            findings.append(
                Finding(
                    entity_kind=EntityKind.CVE,
                    entity_value=cve_id,
                    attributes={
                        "summary": v.get("summary", "")[:280],
                        "cvss": severity,
                        "aliases": v.get("aliases", []),
                    },
                    related_to=subject.value,
                    relationship="HAS_VULNERABILITY",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )
        return ToolResult(
            tool=self.name,
            source_category=self.source_category,
            findings=findings,
            evidence=evidence,
        )


def _max_cvss(vuln: dict[str, Any]) -> float | None:
    """Extract the highest CVSS base score present in an OSV record, if any."""
    best: float | None = None
    for sev in vuln.get("severity", []):
        score = sev.get("score", "")
        # OSV stores CVSS vectors; a bare numeric may also appear.
        try:
            val = float(score)
        except (TypeError, ValueError):
            continue
        best = val if best is None else max(best, val)
    return best


async def get_json_post(url: str, payload: dict[str, Any]) -> Any | None:
    """POST JSON and parse the response — a small local helper (OSV needs POST)."""
    import httpx

    from tools.http import USER_AGENT

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url, json=payload, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
            )
            resp.raise_for_status()
            return resp.json()
    except (httpx.HTTPError, ValueError):
        return None
