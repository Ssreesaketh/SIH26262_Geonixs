import os
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.ai_document_service import extract_pdf_pages, evaluate_document, sha256_bytes


def make_pdf(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    payload = doc.tobytes()
    doc.close()
    return payload


def test_extract_pdf_pages_keeps_page_numbers():
    result = extract_pdf_pages(make_pdf("Synthetic demonstration document for review."))
    assert result["page_count"] == 1
    assert result["has_extractable_text"] is True
    assert result["pages"][0]["page"] == 1
    assert "Synthetic demonstration document" in result["text"]


def test_evaluation_fallback_is_explicitly_advisory(monkeypatch):
    monkeypatch.setattr("app.services.ai_document_service.OLLAMA_URL", "")
    report = evaluate_document(make_pdf("Synthetic demonstration document for review."), "OTHER_REGULATORY_DOCUMENT", "synthetic.pdf", [])
    assert report["advisory_only"] is True
    assert report["official_decision"] is False
    assert report["engine_mode"] == "deterministic_fallback"
    assert any("No LLM evaluation" in item for item in report["limitations"])


def test_sha256_is_stable():
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_institution_can_evaluate_own_pdf_but_report_is_advisory(client, institution_token):
    pdf = make_pdf("Synthetic document. Institution: Zenith. Document details for officer review.")
    uploaded = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {institution_token}"},
        data={"document_type": "OTHER_REGULATORY_DOCUMENT", "display_name": "synthetic-ai-review.pdf"},
        files={"file": ("synthetic-ai-review.pdf", pdf, "application/pdf")},
    )
    assert uploaded.status_code == 200, uploaded.text
    document_id = uploaded.json()["id"]
    response = client.post(
        f"/api/v1/ai/documents/{document_id}/evaluate",
        headers={"Authorization": f"Bearer {institution_token}"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["report"]["advisory_only"] is True
    assert payload["report"]["official_decision"] is False
    assert payload["content_sha256"]


def test_regulatory_source_upload_is_admin_only_and_rag_cites_sources(client, admin_token, institution_token):
    pdf = make_pdf("For synthetic test only: an example rule says officers should verify the listed evidence before review.")
    denied = client.post(
        "/api/v1/ai/knowledge/upload",
        headers={"Authorization": f"Bearer {institution_token}"},
        data={"source_title": "Synthetic test source"},
        files={"file": ("source.pdf", pdf, "application/pdf")},
    )
    assert denied.status_code == 403
    indexed = client.post(
        "/api/v1/ai/knowledge/upload",
        headers={"Authorization": f"Bearer {admin_token}"},
        data={"source_title": "Synthetic test source", "source_version": "test-only"},
        files={"file": ("source.pdf", pdf, "application/pdf")},
    )
    assert indexed.status_code == 200, indexed.text
    answer = client.post(
        "/api/v1/ai/ask",
        headers={"Authorization": f"Bearer {institution_token}"},
        json={"question": "What evidence should officers verify before review?"},
    )
    assert answer.status_code == 200, answer.text
    assert answer.json()["sources"]
    assert "Synthetic test source" in answer.text
