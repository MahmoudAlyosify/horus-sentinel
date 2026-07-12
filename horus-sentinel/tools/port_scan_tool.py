"""TCP port scan + service/banner fingerprint — ACTIVE reconnaissance (authorized only).

Performs an asyncio TCP *connect* scan (a full 3-way handshake — no raw packets, no SYN
stealth) across a curated set of common ports on the target's resolved IPs, then reads a
short banner / issues a minimal HTTP probe to identify the listening service. Because it
sends traffic to the target, it runs **only** against authorized, in-scope assets — the
Authorization Engine refuses anything else.

Emits ``Port`` and ``Service`` nodes wired to the IP (``IP -[EXPOSES]-> Service``) so the
offensive analysis can reason over the live attack surface.
"""

from __future__ import annotations

import asyncio
import contextlib

import structlog

from core.config import settings
from core.findings_store import load_findings
from schemas.auth import AuthContext
from schemas.findings import EntityKind, Evidence, Finding, ToolResult
from schemas.roe import Classification, SourceCategory
from schemas.subject import Subject
from tools.base import IntelTool

log = structlog.get_logger("horus.tool.portscan")

# Well-known service labels for the ports we scan (best-effort identity before banner).
_PORT_SERVICE = {
    21: "ftp",
    22: "ssh",
    23: "telnet",
    25: "smtp",
    53: "dns",
    80: "http",
    110: "pop3",
    111: "rpcbind",
    135: "msrpc",
    139: "netbios-ssn",
    143: "imap",
    443: "https",
    445: "smb",
    993: "imaps",
    995: "pop3s",
    1723: "pptp",
    3306: "mysql",
    3389: "rdp",
    5432: "postgresql",
    5900: "vnc",
    6379: "redis",
    8080: "http-alt",
    8443: "https-alt",
    8000: "http-alt",
    8888: "http-alt",
    9200: "elasticsearch",
    27017: "mongodb",
}
_HTTP_PORTS = {80, 8080, 8000, 8888}
_TLS_PORTS = {443, 8443}


class PortScanTool(IntelTool):
    """Active TCP connect scan + light banner grab against authorized IPs."""

    name = "port_scan"
    classification = Classification.ACTIVE
    source_category = SourceCategory.ACTIVE_RECON
    cache_ttl = 600

    async def run(self, subject: Subject, ctx: AuthContext) -> ToolResult:
        targets = self._targets(ctx, subject)
        ports = self._ports()
        sem = asyncio.Semaphore(max(1, settings.active_scan_concurrency))

        findings: list[Finding] = []
        evidence: list[Evidence] = []
        for ip in targets:
            results = await asyncio.gather(
                *(self._probe(sem, ip, p) for p in ports), return_exceptions=False
            )
            open_ports = [r for r in results if r is not None]
            for port, banner in open_ports:
                service = _PORT_SERVICE.get(port, "unknown")
                ev = Evidence(
                    source=self.name,
                    source_category=self.source_category,
                    summary=f"Open port {ip}:{port} ({service})"
                    + (f" — banner: {banner[:80]}" if banner else ""),
                )
                evidence.append(ev)
                svc_value = f"{ip}:{port}"
                findings.append(
                    Finding(
                        entity_kind=EntityKind.PORT,
                        entity_value=svc_value,
                        attributes={
                            "port": port,
                            "service": service,
                            "state": "open",
                            "internet_facing": True,
                            "banner": banner or "",
                        },
                        related_to=ip,
                        relationship="HAS_OPEN_PORT",
                        evidence=[ev],
                        produced_by=self.name,
                    )
                )
                findings.append(
                    Finding(
                        entity_kind=EntityKind.SERVICE,
                        entity_value=svc_value,
                        attributes={
                            "port": port,
                            "protocol": service,
                            "internet_facing": True,
                            "banner": banner or "",
                        },
                        related_to=ip,
                        relationship="EXPOSES",
                        evidence=[ev],
                        produced_by=self.name,
                    )
                )
            log.info("port_scan_host", ip=ip, scanned=len(ports), open=len(open_ports))
        return ToolResult(
            tool=self.name,
            source_category=self.source_category,
            findings=findings,
            evidence=evidence,
        )

    def _targets(self, ctx: AuthContext, subject: Subject) -> list[str]:
        """IPs discovered so far for this job (from DNS/active-DNS). Falls back to none."""
        prior = load_findings(ctx.job_id)
        ips = sorted({f.entity_value for f in prior if f.entity_kind == EntityKind.IP})
        return ips

    def _ports(self) -> list[int]:
        out: list[int] = []
        for tok in settings.active_scan_ports.split(","):
            tok = tok.strip()
            if tok.isdigit():
                out.append(int(tok))
        return out

    async def _probe(self, sem: asyncio.Semaphore, ip: str, port: int) -> tuple[int, str] | None:
        """Connect to ip:port; if open, grab a short banner. Returns (port, banner) or None."""
        async with sem:
            try:
                fut = asyncio.open_connection(ip, port)
                reader, writer = await asyncio.wait_for(fut, timeout=settings.active_scan_timeout_s)
            except (TimeoutError, OSError):
                return None
            banner = ""
            try:
                banner = await self._grab_banner(reader, writer, ip, port)
            except Exception:  # banner is best-effort; the open state already matters
                pass
            finally:
                writer.close()
                with contextlib.suppress(Exception):
                    await writer.wait_closed()
            return port, banner

    async def _grab_banner(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, ip: str, port: int
    ) -> str:
        """Read a service banner. For HTTP ports send a minimal request first."""
        n = settings.active_banner_bytes
        if port in _HTTP_PORTS:
            writer.write(f"HEAD / HTTP/1.0\r\nHost: {ip}\r\n\r\n".encode())
            with contextlib.suppress(Exception):
                await writer.drain()
        try:
            data = await asyncio.wait_for(reader.read(n), timeout=settings.active_scan_timeout_s)
        except (TimeoutError, OSError):
            return ""
        text = data.decode("latin-1", errors="replace").strip()
        # For HTTP, keep just the Server header line if present.
        if port in _HTTP_PORTS or port in _TLS_PORTS:
            for line in text.splitlines():
                if line.lower().startswith("server:"):
                    return line.strip()
        return text.splitlines()[0].strip() if text else ""
