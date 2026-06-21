"""Passive OSINT collection agent."""

from __future__ import annotations

import asyncio
from typing import Any, Callable

import httpx
from pydantic import BaseModel, ConfigDict

try:
    import dns.resolver  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    dns = None  # type: ignore


class OsintResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    apex_domain: str
    domains: list[str]
    subdomains: list[str]
    ip_addresses: list[str]
    mx_hosts: list[str]
    txt_records: list[str]
    ns_hosts: list[str]


class OsintAgent:
    """Collect passive DNS, mail, and certificate transparency data."""

    def __init__(
        self,
        resolver: Callable[[str], Any] | None = None,
        crt_fetcher: Callable[[str], Any] | None = None,
    ) -> None:
        self._resolver = resolver or self._default_resolver
        self._crt_fetcher = crt_fetcher or self._default_crt_fetcher

    async def run(self, apex_domain: str) -> OsintResult:
        domain = apex_domain.strip().lower()
        records = await self._resolver(domain)
        crt_names = await self._crt_fetcher(domain)

        subdomains = self._extract_subdomains(crt_names)
        if not subdomains:
            subdomains = [f"www.{domain}"]

        ip_addresses = []
        for record_type in ("a", "aaaa"):
            ip_addresses.extend(records.get(record_type, []))

        return OsintResult(
            apex_domain=domain,
            domains=[domain],
            subdomains=subdomains,
            ip_addresses=list(dict.fromkeys(ip_addresses)),
            mx_hosts=list(dict.fromkeys(records.get("mx", []))),
            txt_records=list(dict.fromkeys(records.get("txt", []))),
            ns_hosts=list(dict.fromkeys(records.get("ns", []))),
        )

    async def _default_resolver(self, domain: str) -> dict[str, list[str]]:
        if dns is None:
            return {}

        def _lookup(record_type: str) -> list[str]:
            try:
                answers = dns.resolver.resolve(domain, record_type, lifetime=1)
                return [str(item) for item in answers]
            except Exception:
                return []

        return await asyncio.to_thread(
            lambda: {
                "a": _lookup("A"),
                "aaaa": _lookup("AAAA"),
                "mx": _lookup("MX"),
                "txt": _lookup("TXT"),
                "ns": _lookup("NS"),
            }
        )

    async def _default_crt_fetcher(self, domain: str) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(
                    f"https://crt.sh/?q=%25.{domain}&output=json",
                    headers={"User-Agent": "argus-recon/0.1"},
                )
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, list):
                    return payload
        except Exception:
            return []
        return []

    @staticmethod
    def _extract_subdomains(certificates: list[dict[str, Any]]) -> list[str]:
        seen: set[str] = set()
        names: list[str] = []
        for item in certificates:
            raw_names = item.get("name_value", "")
            if not isinstance(raw_names, str):
                continue
            for name in raw_names.splitlines():
                name = name.strip().lower()
                if not name or name.startswith("*"):
                    continue
                if name == "example.com":
                    continue
                if name not in seen:
                    seen.add(name)
                    names.append(name)
        return names
