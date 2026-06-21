"""Passive web fingerprinting agent."""

from __future__ import annotations

import httpx
from pydantic import BaseModel, ConfigDict


class WebFingerprintResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hosts: list[dict[str, str | None]]


class WebAgent:
    """Fetch a lightweight response from each host and capture header hints."""

    async def run(self, hosts: list[str]) -> WebFingerprintResult:
        fingerprints: list[dict[str, str | None]] = []
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            for host in hosts:
                try:
                    response = await client.get(f"https://{host}/", headers={"User-Agent": "argus-recon/0.1"})
                    fingerprints.append(
                        {
                            "host": host,
                            "server": response.headers.get("server"),
                            "content_type": response.headers.get("content-type"),
                            "title": self._extract_title(response.text),
                        }
                    )
                except Exception:
                    fingerprints.append({"host": host, "server": None, "content_type": None, "title": None})
        return WebFingerprintResult(hosts=fingerprints)

    @staticmethod
    def _extract_title(html: str) -> str | None:
        start = html.lower().find("<title>")
        if start == -1:
            return None
        end = html.lower().find("</title>", start)
        if end == -1:
            return None
        return html[start + 7 : end].strip()
