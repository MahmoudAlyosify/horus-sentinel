"""Setup routes — drive first-run configuration from the Command Center UI.

``GET /setup/status`` tells the UI whether it still needs to prompt for a Hugging Face token;
``POST /setup/hf-token`` validates a token against HF and persists it. The refusal here is
gentle (400 with a reason) — a bad token is a user error, not a server fault.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.config import settings, update_env
from core.setup_wizard import save_hf_config, setup_status

router = APIRouter(prefix="/setup", tags=["setup"])


class LanguageRequest(BaseModel):
    """Switch the system/report language."""

    language: str = Field(..., description="ar (Arabic, RTL) | en (English).")


class HFTokenRequest(BaseModel):
    """The analyst's Hugging Face credentials collected at first run."""

    token: str = Field(..., description="Hugging Face access token (read scope is enough).")
    model_id: str | None = Field(default=None, description="Override the HF model id.")
    endpoint_url: str | None = Field(
        default=None, description="Dedicated HF Inference Endpoint URL (optional)."
    )
    backend: str | None = Field(
        default=None, description="hybrid | hf_serverless | hf_endpoint | ollama."
    )


@router.get("/status")
async def get_setup_status() -> dict:
    """Whether first-run setup is complete, plus per-transport reachability."""
    return await setup_status()


@router.post("/language")
async def set_language(req: LanguageRequest) -> dict:
    """Set the system/report language (ar | en). Persists to .env + live settings."""
    lang = req.language.strip().lower()
    if lang not in ("ar", "en"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="language must be 'ar' or 'en'.",
        )
    update_env({"REPORT_LANGUAGE": lang})
    return {"ok": True, "report_language": settings.report_language}


@router.post("/hf-token")
async def set_hf_token(req: HFTokenRequest) -> dict:
    """Validate + save the HF token. 400 (with reason) if the token is rejected by HF."""
    ok, info = await save_hf_config(
        req.token,
        model_id=req.model_id,
        endpoint_url=req.endpoint_url,
        backend=req.backend,
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Hugging Face token rejected: {info}",
        )
    return {"ok": True, "hf_username": info, "status": await setup_status()}
