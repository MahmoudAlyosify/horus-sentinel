"""Conversational endpoint — a direct chat with the fine-tuned Horus-OSINT model.

This backs the "HORUS reasoning" chat in the Command Center. The analyst's free-form
question goes straight to the self-hosted fine-tuned model (Ollama, with the online HF
transport as a fallback per ``BRAIN_BACKEND``). Unlike the grounded assessment pipeline,
this is the model reasoning conversationally, so the answer is **not** corpus-grounded —
the UI labels it as such. If no transport is reachable a graceful message is returned.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from core.config import settings
from horus_brain.brain import get_brain
from reporting.chat_report import render_chat_html, render_chat_pdf

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """A single free-form question for the model."""

    query: str = Field(..., min_length=1, description="The analyst's free-form question.")
    language: str | None = Field(
        default=None, description="ar | en (defaults to the configured report language)."
    )


class ChatReportRequest(BaseModel):
    """A Horus-OSINT chat exchange to render as a downloadable report."""

    question: str = Field(..., min_length=1, description="The analyst's question.")
    answer: str = Field(..., min_length=1, description="The Horus-OSINT answer to render.")
    generated_by: str | None = Field(
        default=None, description="Transport that authored the answer."
    )
    language: str | None = Field(default=None, description="ar | en (defaults to report language).")
    fmt: str = Field(default="pdf", description="pdf | html")


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


def _norm_lang(language: str | None) -> str:
    lang = (language or settings.report_language or "en").lower()
    return lang if lang in ("ar", "en") else "en"


@router.post("")
async def chat(req: ChatRequest) -> dict:
    """Answer a free-form question with the fine-tuned model. Never corpus-grounded."""
    lang = _norm_lang(req.language)
    answer, generated_by = await get_brain().chat(req.query, lang)
    if not answer:
        return {"answer": _OFFLINE_MSG[lang], "generated_by": "offline", "grounded": False}
    return {"answer": answer, "generated_by": generated_by, "grounded": False}


@router.post("/report")
async def chat_report(req: ChatReportRequest) -> Response:
    """Render a Horus-OSINT chat exchange as a downloadable branded report (pdf | html)."""
    lang = _norm_lang(req.language)
    fmt = req.fmt.lower()
    if fmt not in ("pdf", "html"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="fmt must be 'pdf' or 'html'."
        )
    if fmt == "html":
        html = render_chat_html(
            req.question, req.answer, generated_by=req.generated_by or "", language=lang
        )
        return Response(
            content=html,
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=horus-chat-report.html"},
        )
    pdf = render_chat_pdf(
        req.question, req.answer, generated_by=req.generated_by or "", language=lang
    )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=horus-chat-report.pdf"},
    )
