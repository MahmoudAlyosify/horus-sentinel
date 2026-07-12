"""Active web crawler / scraper — content discovery on an AUTHORIZED web target.

Unlike the passive single-page fingerprint, this actively crawls the target site within a
page/depth budget (same host only), fetching ``robots.txt`` and ``sitemap.xml`` and parsing
each page for links, forms, e-mail addresses and technology hints. It sends many requests to
the target, so it runs **only** against an authorized, in-scope asset (enforced upstream).

Emits ``Endpoint`` nodes (discovered URLs/paths) plus ``Email`` and ``Technology`` findings
that enrich the offensive attack-surface view. Politeness: bounded budget, courteous
User-Agent, and it honours the crawl budget from config.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import structlog

from core.config import settings
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import Classification, SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool
from tools.http import USER_AGENT

log = structlog.get_logger("horus.tool.webcrawl")

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Lightweight technology fingerprints from response headers / body markers.
_TECH_MARKERS = {
    "wordpress": "WordPress",
    "wp-content": "WordPress",
    "drupal": "Drupal",
    "joomla": "Joomla",
    "laravel": "Laravel",
    "django": "Django",
    "react": "React",
    "next.js": "Next.js",
    "nuxt": "Nuxt",
    "vue": "Vue.js",
    "angular": "Angular",
    "jquery": "jQuery",
    "bootstrap": "Bootstrap",
    "nginx": "nginx",
    "apache": "Apache",
}


class _LinkFormParser(HTMLParser):
    """Extracts hrefs, form actions/methods, and script srcs from a page."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.forms: list[dict[str, str]] = []
        self.scripts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "form":
            self.forms.append({"action": a.get("action", ""), "method": a.get("method", "get")})
        elif tag == "script" and a.get("src"):
            self.scripts.append(a["src"])


class WebCrawlTool(IntelTool):
    """Active, budgeted crawler/scraper for an authorized web target."""

    name = "web_crawl"
    classification = Classification.ACTIVE
    source_category = SourceCategory.WEB_CRAWL
    cache_ttl = 600

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        host = subject.value.lower().lstrip(".")
        root = f"https://{host}/"
        findings: list[Finding] = []
        evidence: list[Evidence] = []
        emails: set[str] = set()
        techs: set[str] = set()

        async with httpx.AsyncClient(
            timeout=settings.active_crawl_timeout_s,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        ) as client:
            # Compliance-by-construction (master plan Part 4.2): load robots.txt first and
            # honour can_fetch() before every request. Even on an authorized owned target we
            # stay polite — this is a code-level control, not a guideline.
            self._robots = await self._load_robots(client, host, root, findings, evidence)
            await self._fetch_wellknown(client, host, root, findings, evidence)
            await self._crawl(client, host, root, findings, evidence, emails, techs)

        for email in sorted(emails):
            ev = Evidence(
                source=self.name,
                source_category=self.source_category,
                summary=f"Email harvested from {host}: {email}",
            )
            evidence.append(ev)
            findings.append(
                Finding(
                    entity_kind=EntityKind.EMAIL,
                    entity_value=email,
                    attributes={"discovery": "active_crawl"},
                    related_to=host,
                    relationship="MENTIONED_ON",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )
        for tech in sorted(techs):
            ev = Evidence(
                source=self.name,
                source_category=self.source_category,
                summary=f"Technology marker on {host}: {tech}",
            )
            evidence.append(ev)
            findings.append(
                Finding(
                    entity_kind=EntityKind.TECHNOLOGY,
                    entity_value=tech,
                    attributes={"discovery": "active_crawl"},
                    related_to=host,
                    relationship="RUNS",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )

        log.info(
            "web_crawl_complete",
            host=host,
            endpoints=sum(1 for f in findings if f.entity_kind == EntityKind.ENDPOINT),
            emails=len(emails),
            techs=len(techs),
        )
        return ToolResult(
            tool=self.name,
            source_category=self.source_category,
            findings=findings,
            evidence=evidence,
        )

    async def _load_robots(
        self,
        client: httpx.AsyncClient,
        host: str,
        root: str,
        findings: list[Finding],
        evidence: list[Evidence],
    ) -> RobotFileParser:
        """Fetch + parse robots.txt so ``can_fetch`` gates every subsequent request.

        Also records robots.txt and its Disallow paths as *noted* endpoints (recon value:
        those paths exist) — we never crawl the disallowed ones, we only report them.
        """
        rp = RobotFileParser()
        url = urljoin(root, "robots.txt")
        rp.set_url(url)
        text = ""
        try:
            resp = await client.get(url)
            if resp.status_code < 400 and resp.text:
                text = resp.text
        except httpx.HTTPError:
            pass
        rp.parse(text.splitlines() if text else [])
        ev = Evidence(
            source=self.name,
            source_category=self.source_category,
            summary="Loaded robots.txt; honouring can_fetch() before every request.",
        )
        evidence.append(ev)
        if text:
            findings.append(
                Finding(
                    entity_kind=EntityKind.ENDPOINT,
                    entity_value=url,
                    attributes={"source": "robots.txt"},
                    related_to=host,
                    relationship="HAS_ENDPOINT",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )
            for m in re.finditer(r"(?i)Disallow:\s*(\S+)", text):
                findings.append(
                    Finding(
                        entity_kind=EntityKind.ENDPOINT,
                        entity_value=urljoin(root, m.group(1)),
                        attributes={"source": "robots-disallow", "note": "recorded, not crawled"},
                        related_to=host,
                        relationship="HAS_ENDPOINT",
                        evidence=[ev],
                        produced_by=self.name,
                    )
                )
        return rp

    def _allowed(self, url: str) -> bool:
        """robots.txt gate. Missing policy → allowed (standard); disallowed → skip + log."""
        rp = getattr(self, "_robots", None)
        if rp is None:
            return True
        try:
            ok = rp.can_fetch(USER_AGENT, url)
        except Exception:
            return True
        if not ok:
            log.info("robots_skip", url=url)
        return ok

    async def _fetch_wellknown(
        self,
        client: httpx.AsyncClient,
        host: str,
        root: str,
        findings: list[Finding],
        evidence: list[Evidence],
    ) -> None:
        """Fetch sitemap.xml — a classic content-discovery seed (robots already fetched)."""
        for path in ("sitemap.xml",):
            url = urljoin(root, path)
            if not self._allowed(url):
                continue
            try:
                resp = await client.get(url)
            except httpx.HTTPError:
                continue
            if resp.status_code >= 400:
                continue
            ev = Evidence(
                source=self.name,
                source_category=self.source_category,
                summary=f"Fetched {path} ({resp.status_code}, {len(resp.text)} bytes)",
            )
            evidence.append(ev)
            findings.append(
                Finding(
                    entity_kind=EntityKind.ENDPOINT,
                    entity_value=url,
                    attributes={"status": resp.status_code, "source": path},
                    related_to=host,
                    relationship="HAS_ENDPOINT",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )
            # Pull Disallow paths from robots as extra endpoints to note.
            if path == "robots.txt":
                for m in re.finditer(r"(?i)Disallow:\s*(\S+)", resp.text):
                    disallowed = urljoin(root, m.group(1))
                    findings.append(
                        Finding(
                            entity_kind=EntityKind.ENDPOINT,
                            entity_value=disallowed,
                            attributes={"source": "robots-disallow"},
                            related_to=host,
                            relationship="HAS_ENDPOINT",
                            evidence=[ev],
                            produced_by=self.name,
                        )
                    )

    async def _crawl(
        self,
        client: httpx.AsyncClient,
        host: str,
        root: str,
        findings: list[Finding],
        evidence: list[Evidence],
        emails: set[str],
        techs: set[str],
    ) -> None:
        """BFS crawl within the page/depth budget, same host only."""
        seen: set[str] = set()
        queue: list[tuple[str, int]] = [(root, 0)]
        pages = 0
        while queue and pages < settings.active_crawl_max_pages:
            url, depth = queue.pop(0)
            if url in seen or depth > settings.active_crawl_max_depth:
                continue
            seen.add(url)
            if not self._allowed(url):  # robots.txt disallows — skip + log (compliance)
                continue
            resp = await self._polite_get(client, url)
            if resp is None:
                continue
            pages += 1
            ctype = resp.headers.get("content-type", "")
            ev = Evidence(
                source=self.name,
                source_category=self.source_category,
                summary=f"Crawled {url} ({resp.status_code}, {ctype.split(';')[0]})",
            )
            evidence.append(ev)
            findings.append(
                Finding(
                    entity_kind=EntityKind.ENDPOINT,
                    entity_value=url,
                    attributes={
                        "status": resp.status_code,
                        "content_type": ctype.split(";")[0],
                        "depth": depth,
                        "forms": 0,
                    },
                    related_to=host,
                    relationship="HAS_ENDPOINT",
                    evidence=[ev],
                    produced_by=self.name,
                )
            )
            if "html" not in ctype:
                continue
            body = resp.text
            emails.update(_EMAIL_RE.findall(body))
            self._detect_tech(resp.headers, body, techs)
            parser = _LinkFormParser()
            with_forms = 0
            try:
                parser.feed(body)
                with_forms = len(parser.forms)
            except Exception:
                pass
            if with_forms:
                findings[-1].attributes["forms"] = with_forms
                ev2 = Evidence(
                    source=self.name,
                    source_category=self.source_category,
                    summary=f"{with_forms} form(s) on {url} (input surface)",
                )
                evidence.append(ev2)
            for href in parser.links:
                nxt = urljoin(url, href)
                p = urlparse(nxt)
                if p.scheme in ("http", "https") and p.netloc.lower().split(":")[0] == host:
                    clean = nxt.split("#")[0]
                    if clean not in seen:
                        queue.append((clean, depth + 1))

    async def _polite_get(self, client: httpx.AsyncClient, url: str) -> httpx.Response | None:
        """GET with exponential backoff on 429/503 (never behave like a DoS)."""
        import asyncio

        delay = 0.5
        for _attempt in range(3):
            try:
                resp = await client.get(url)
            except httpx.HTTPError:
                return None
            if resp.status_code in (429, 503):
                retry_after = resp.headers.get("retry-after")
                wait = float(retry_after) if (retry_after and retry_after.isdigit()) else delay
                log.info("crawl_backoff", url=url, status=resp.status_code, wait=wait)
                await asyncio.sleep(min(wait, 5.0))
                delay *= 2
                continue
            return resp
        return None

    @staticmethod
    def _detect_tech(headers: httpx.Headers, body: str, techs: set[str]) -> None:
        server = headers.get("server", "")
        powered = headers.get("x-powered-by", "")
        hay = f"{server} {powered} {body[:6000]}".lower()
        for marker, label in _TECH_MARKERS.items():
            if marker in hay:
                techs.add(label)
