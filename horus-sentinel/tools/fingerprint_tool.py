"""Passive web fingerprinting (master plan Part 3.3).

A single, polite HTTPS request to a web-facing subject, then signature-matching on the
response headers to infer the technology footprint: web server, framework, CMS, CDN/WAF,
cloud provider and TLS posture. One request, no crawling, no probing — passive by design,
and (per the authorization engine) only ever run against owned/in-scope domains.
"""

from __future__ import annotations

from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool
from tools.http import get_text

# header substring -> (technology name, category). Small, high-signal signature set.
_HEADER_SIGNATURES: list[tuple[str, str, str, str]] = [
    # header, needle, tech, category
    ("server", "nginx", "nginx", "web_server"),
    ("server", "apache", "Apache", "web_server"),
    ("server", "cloudflare", "Cloudflare", "cdn_waf"),
    ("server", "microsoft-iis", "IIS", "web_server"),
    ("server", "gws", "Google Web Server", "web_server"),
    ("x-powered-by", "php", "PHP", "framework"),
    ("x-powered-by", "asp.net", "ASP.NET", "framework"),
    ("x-powered-by", "express", "Express", "framework"),
    ("x-generator", "wordpress", "WordPress", "cms"),
    ("x-generator", "drupal", "Drupal", "cms"),
    ("cf-ray", "", "Cloudflare", "cdn_waf"),
    ("x-amz-cf-id", "", "AWS CloudFront", "cdn"),
    ("x-akamai-transformed", "", "Akamai", "cdn"),
    ("x-sucuri-id", "", "Sucuri WAF", "cdn_waf"),
    ("x-served-by", "fastly", "Fastly", "cdn"),
]


class WebInfraTool(IntelTool):
    """Fingerprint a web-facing domain's public technology footprint (passive)."""

    name = "fingerprint"
    source_category = SourceCategory.WEB_INFRA
    cache_ttl = 21600

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        fetched = await get_text(f"https://{subject.value}")
        if fetched is None:
            return ToolResult(
                tool=self.name,
                source_category=self.source_category,
                error=f"could not fetch https://{subject.value} (network error)",
            )
        status, headers, _body = fetched

        techs = self._match_technologies(headers)
        service_id = f"{subject.value}:443"
        ev = Evidence(
            source=self.name,
            source_category=self.source_category,
            summary=(
                f"HTTPS {subject.value}: status={status}, server={headers.get('server', 'n/a')}, "
                f"tech={', '.join(t[0] for t in techs) or 'none matched'}"
            ),
            raw_ref=Evidence.digest(headers),
        )

        findings: list[Finding] = [
            Finding(
                entity_kind=EntityKind.SERVICE,
                entity_value=service_id,
                attributes={
                    "port": 443,
                    "scheme": "https",
                    "status": status,
                    "internet_facing": True,
                    "server_header": headers.get("server"),
                    "hsts": "strict-transport-security" in headers,
                },
                related_to=subject.value,
                relationship="SERVES",
                evidence=[ev],
                produced_by=self.name,
            )
        ]
        for tech_name, category in techs:
            findings.append(
                Finding(
                    entity_kind=EntityKind.TECHNOLOGY,
                    entity_value=tech_name,
                    attributes={"category": category},
                    related_to=service_id,
                    relationship="RUNS",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )
        return ToolResult(
            tool=self.name,
            source_category=self.source_category,
            findings=findings,
            evidence=[ev],
        )

    @staticmethod
    def _match_technologies(headers: dict[str, str]) -> list[tuple[str, str]]:
        found: dict[str, str] = {}
        for header, needle, tech, category in _HEADER_SIGNATURES:
            value = headers.get(header, "").lower()
            if header in headers and (needle == "" or needle in value):
                found[tech] = category
        return sorted(found.items())
