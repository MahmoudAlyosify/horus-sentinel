"""Chat endpoint tests — the free-form 'Horus-OSINT chat' (POST /chat).

Under the hermetic test config the brain is the Ollama-only backend, so mocking the
self-hosted endpoint fully controls the model. Verifies the analyst's actual question
drives the answer (the previous UI bug replied with a canned demo regardless of input),
and that an unreachable model degrades to a graceful message instead of erroring.
"""

import httpx
import respx
from fastapi.testclient import TestClient

from api.main import app
from horus_brain.horus_provider import horus_provider

client = TestClient(app)


def test_chat_returns_model_answer():
    answer = "During 2013 Egypt experienced major political upheaval centered on Cairo."
    with respx.mock(assert_all_called=True) as router:
        route = router.post(horus_provider.endpoint).mock(
            return_value=httpx.Response(200, json={"response": answer})
        )
        resp = client.post(
            "/chat", json={"query": "What happened in Egypt in 2013?", "language": "en"}
        )
        # The user's actual question must be forwarded to the model, not discarded.
        sent = route.calls.last.request
        assert b"Egypt in 2013" in sent.content

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["answer"] == answer
    assert body["grounded"] is False
    assert body["generated_by"] != "offline"


def test_chat_degrades_gracefully_when_model_unreachable():
    with respx.mock(assert_all_called=False) as router:
        router.post(horus_provider.endpoint).mock(side_effect=httpx.ConnectError("refused"))
        resp = client.post("/chat", json={"query": "أعطني تقييمًا", "language": "ar"})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["generated_by"] == "offline"
    assert body["answer"]  # a non-empty graceful Arabic message


def test_chat_rejects_empty_query():
    # An empty query fails validation (min_length=1) before any model call is attempted.
    resp = client.post("/chat", json={"query": ""})
    assert resp.status_code == 422


def test_chat_report_pdf_is_real_pdf():
    resp = client.post(
        "/chat/report",
        json={
            "question": "What happened in Egypt in 2013?",
            "answer": "In 2013 Egypt experienced major political upheaval centered on Cairo.",
            "generated_by": "horus-selfhosted",
            "language": "en",
            "fmt": "pdf",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert "attachment" in resp.headers["content-disposition"]
    assert resp.content[:5] == b"%PDF-"


def test_chat_report_html_contains_qa():
    resp = client.post(
        "/chat/report",
        json={
            "question": "ما هو الوضع؟",
            "answer": "تقييم موجز للوضع.",
            "generated_by": "horus-selfhosted",
            "language": "ar",
            "fmt": "html",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/html")
    body = resp.text
    assert "ما هو الوضع؟" in body
    assert "تقييم موجز للوضع." in body
    assert "حورس سنتينل" in body  # branded


def test_chat_report_rejects_bad_format():
    resp = client.post(
        "/chat/report",
        json={"question": "q", "answer": "a", "fmt": "xml"},
    )
    assert resp.status_code == 400
