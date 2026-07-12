"""Conversational endpoint — a direct chat with the fine-tuned Horus-OSINT model.

This backs the "HORUS reasoning" chat in the Command Center. The analyst's free-form
question goes straight to the self-hosted fine-tuned model (Ollama, with the online HF
transport as a fallback per ``BRAIN_BACKEND``). Unlike the grounded assessment pipeline,
this is the model reasoning conversationally, so the answer is **not** corpus-grounded —
the UI labels it as such. If no transport is reachable a graceful message is returned.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.config import settings
from horus_brain.brain import get_brain

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """A single free-form question for the model."""

    query: str = Field(..., min_length=1, description="The analyst's free-form question.")
    language: str | None = Field(
        default=None, description="ar | en (defaults to the configured report language)."
    )


_OFFLINE_MSG = {
    "ar": (
        "النموذج غير متاح حاليًا. تأكد من تشغيل Ollama محليًا أو ضبط رمز Hugging Face صالح، "
        "ثم أعد المحاولة."
    ),
    "en": (
        "The model is currently unavailable. Ensure Ollama is running locally or a valid "
        "Hugging Face token is set, then try again."
    ),
}


@router.post("")
async def chat(req: ChatRequest) -> dict:
    """Answer a free-form question with the fine-tuned model. Never corpus-grounded."""
    lang = (req.language or settings.report_language or "en").lower()
    if lang not in ("ar", "en"):
        lang = "en"
    answer, generated_by = await get_brain().chat(req.query, lang)
    if not answer:
        return {"answer": _OFFLINE_MSG[lang], "generated_by": "offline", "grounded": False}
    return {"answer": answer, "generated_by": generated_by, "grounded": False}
