"""Shared async HTTP helpers for passive, read-only source lookups.

All collection is passive: these helpers only issue GETs to public endpoints (RDAP,
crt.sh, OSV, reputation APIs). Timeouts and a courteous User-Agent are applied centrally.
Network failures return ``None`` so a source outage degrades gracefully into an empty
finding set rather than killing a job.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

log = structlog.get_logger("horus.http")

USER_AGENT = (
    "HORUS-Sentinel/0.1 (passive OSINT; +https://github.com/MahmoudAlyosify/horus-sentinel)"
)
DEFAULT_TIMEOUT = 15.0


async def get_json(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any | None:
    """GET a URL and parse JSON. Returns ``None`` on any network/parse error."""
    merged = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        merged.update(headers)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, params=params, headers=merged)
            resp.raise_for_status()
            return resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        log.debug("http_get_failed", url=url, error=str(exc))
        return None


async def get_text(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[int, dict[str, str], str] | None:
    """GET a URL and return (status, headers, text). ``None`` on network error.

    Used for passive web fingerprinting — a single polite page fetch, no crawling.
    """
    merged = {"User-Agent": USER_AGENT}
    if headers:
        merged.update(headers)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers=merged)
            return resp.status_code, {k.lower(): v for k, v in resp.headers.items()}, resp.text
    except httpx.HTTPError as exc:
        log.debug("http_get_text_failed", url=url, error=str(exc))
        return None
