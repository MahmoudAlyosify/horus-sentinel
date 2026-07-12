"""First-run setup — collect and validate the Hugging Face token (master plan: online brain).

On a fresh install the online brain has no credentials. Rather than hard-code anything, the
platform asks the analyst for their HF token on first run — from the Command Center UI (the
primary path) or this module's CLI. The token is validated against the HF ``whoami`` API and
persisted to ``.env`` so it survives restarts. Nothing is stored unless it validates.

Run the CLI wizard directly with:  ``python -m core.setup_wizard``
"""

from __future__ import annotations

import asyncio

import httpx
import structlog

from core.config import settings, update_env

log = structlog.get_logger("horus.setup")

_WHOAMI = "https://huggingface.co/api/whoami-v2"

# Backends that need an HF token to reach the online model.
_HF_BACKENDS = {"hybrid", "hf_serverless", "hf_endpoint"}


async def validate_hf_token(token: str) -> tuple[bool, str]:
    """Validate a token against the HF whoami API. Returns (ok, username-or-error-message)."""
    token = (token or "").strip()
    if not token:
        return False, "empty token"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(_WHOAMI, headers={"Authorization": f"Bearer {token}"})
    except httpx.HTTPError as exc:
        return False, f"network error: {exc}"
    if resp.status_code == 200:
        name = resp.json().get("name", "unknown")
        return True, name
    if resp.status_code in (401, 403):
        return False, "invalid or unauthorized token"
    return False, f"unexpected HF response: HTTP {resp.status_code}"


async def save_hf_config(
    token: str,
    *,
    model_id: str | None = None,
    endpoint_url: str | None = None,
    backend: str | None = None,
) -> tuple[bool, str]:
    """Validate the token (unless a token-free backend is chosen), then persist config.

    Selecting the ``ollama`` backend needs no token (sovereign, self-hosted): we persist the
    backend choice and return without contacting HF. Returns (ok, message).
    """
    if backend == "ollama":
        update_env({"BRAIN_BACKEND": "ollama"})
        log.info("brain_backend_set", backend="ollama")
        return True, "ollama (self-hosted, no token needed)"

    ok, info = await validate_hf_token(token)
    if not ok:
        return False, info
    values: dict[str, str] = {"HF_TOKEN": token.strip()}
    if model_id:
        values["HF_MODEL_ID"] = model_id.strip()
    if endpoint_url:
        values["HF_ENDPOINT_URL"] = endpoint_url.strip()
    if backend:
        values["BRAIN_BACKEND"] = backend.strip()
    update_env(values)
    log.info("hf_config_saved", username=info, backend=settings.brain_backend)
    return True, info


async def setup_status() -> dict:
    """A snapshot the UI/CLI use to decide whether first-run setup is still needed."""
    from horus_brain.brain import get_brain

    backend = settings.brain_backend
    needs_token = backend in _HF_BACKENDS
    has_token = bool(settings.hf_token)
    token_ok = False
    username = ""
    if has_token:
        token_ok, username = await validate_hf_token(settings.hf_token)

    brain_health = await get_brain().health()
    online_ready = any(v for k, v in brain_health.items() if k.startswith("hf-"))
    ollama_ready = any(v for k, v in brain_health.items() if k.startswith("horus-selfhosted"))

    # "Configured" = either the online brain is ready, or a local self-hosted brain answers,
    # or the backend doesn't need a token at all. The platform still runs (offline synthesis)
    # even when this is False — setup only unlocks *model-authored* narration.
    configured = (token_ok and online_ready) or ollama_ready or not needs_token

    return {
        "brain_backend": backend,
        "report_language": settings.report_language,
        "needs_hf_token": needs_token,
        "has_hf_token": has_token,
        "hf_token_valid": token_ok,
        "hf_username": username,
        "hf_model_id": settings.hf_model_id,
        "hf_endpoint_configured": bool(settings.hf_endpoint_url),
        "online_ready": online_ready,
        "ollama_ready": ollama_ready,
        "transports": brain_health,
        "configured": configured,
    }


def _cli() -> None:
    """Interactive first-run wizard for a terminal."""
    print("=" * 60)
    print("  HORUS Sentinel — إعداد أول تشغيل / First-run setup")
    print("=" * 60)
    status = asyncio.run(setup_status())
    print(f"\nBrain backend : {status['brain_backend']}")
    print(f"Report language: {status['report_language']}")
    if status["has_hf_token"] and status["hf_token_valid"]:
        print(f"HF token already valid (user: {status['hf_username']}). Nothing to do.")
        return
    if not status["needs_hf_token"]:
        print("Backend does not require a Hugging Face token. Nothing to do.")
        return

    print("\nأدخل رمز Hugging Face (HF token) للوصول إلى نموذجك أونلاين.")
    print("Get one at: https://huggingface.co/settings/tokens  (read access is enough)")
    token = input("HF token: ").strip()
    if not token:
        print("No token entered — skipped. The platform still runs with offline synthesis.")
        return
    ok, info = asyncio.run(save_hf_config(token))
    if ok:
        print(f"\n[OK] Token validated and saved (user: {info}). Online brain is ready.")
    else:
        print(f"\n[FAILED] {info}. Token not saved.")


if __name__ == "__main__":
    _cli()
