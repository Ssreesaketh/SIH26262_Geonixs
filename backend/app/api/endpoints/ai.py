from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import hashlib
import re
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.core.auth import get_current_user, verify_institution_access, verify_regional_access
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Application, Document, Institution, DocumentEvaluation, RegulatoryChunk, User
from app.services.document_service import DocumentService
from app.services.audit_service import AuditService
from app.services.ai_document_service import extract_pdf_pages, evaluate_document, retrieve_chunks, answer_question, sha256_bytes, _ollama_embed

router = APIRouter()

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)


def _authorize_document(db: Session, doc: Document, user: User) -> None:
    verify_institution_access(user, doc.institution_id)
    if user.role == "REGIONAL_OFFICER":
        institution = db.query(Institution).filter(Institution.id == doc.institution_id).first()
        if not institution:
            raise HTTPException(status_code=404, detail="Institution not found")
        verify_regional_access(user, institution.region_id)


def _evaluation_payload(row: DocumentEvaluation):
    return {"id": row.id, "document_id": row.document_id, "institution_id": row.institution_id,
            "application_id": row.application_id, "status": row.status, "engine_mode": row.engine_mode,
            "content_sha256": row.content_sha256, "report": row.report_json,
            "created_at": row.created_at.isoformat() if row.created_at else None}


@router.post("/documents/{document_id}/evaluate")
def evaluate_uploaded_document(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    _authorize_document(db, doc, current_user)
    if doc.mime_type != "application/pdf" or not doc.storage_key.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="AI evaluation currently supports PDF documents only. Image files must be converted to an authorized PDF first.")
    file_path = DocumentService.get_file_path(doc)
    try:
        content = Path(file_path).read_bytes()
        extracted = extract_pdf_pages(content)
        # Retrieve only curated regulatory chunks using both document metadata and
        # extracted content; uploaded institution files are never indexed as policy.
        context = retrieve_chunks(db, f"{doc.document_type} {doc.display_name} {extracted['text'][:3000]}", limit=4)
        report = evaluate_document(content, doc.document_type, doc.display_name, context, extracted=extracted)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    row = DocumentEvaluation(document_id=doc.id, institution_id=doc.institution_id,
        application_id=doc.application_id, evaluator_user_id=current_user.id,
        status="COMPLETED", content_sha256=sha256_bytes(content), engine_mode=report["engine_mode"], report_json=report)
    db.add(row)
    if doc.application_id:
        AuditService.record_event(db, doc.application_id, current_user, "AI_DOCUMENT_EVALUATED",
            reason=f"Advisory PDF evaluation completed for {doc.display_name}",
            metadata_json={"evaluation_id": row.id, "engine_mode": report["engine_mode"], "findings_count": len(report["findings"])})
    else:
        AuditService.record_system_event(db, current_user, "AI_DOCUMENT_EVALUATED", "Document", doc.id,
            {"engine_mode": report["engine_mode"], "findings_count": len(report["findings"])})
    db.commit()
    db.refresh(row)
    return _evaluation_payload(row)


@router.get("/documents/{document_id}/evaluations")
def list_document_evaluations(document_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    _authorize_document(db, doc, current_user)
    rows = db.query(DocumentEvaluation).filter(DocumentEvaluation.document_id == document_id).order_by(DocumentEvaluation.created_at.desc()).limit(20).all()
    return [_evaluation_payload(row) for row in rows]


@router.post("/knowledge/upload")
async def upload_regulatory_source(file: UploadFile = File(...), source_title: str = Form(...), source_url: Optional[str] = Form(None), source_version: Optional[str] = Form(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "SYSTEM_ADMIN":
        raise HTTPException(status_code=403, detail="Only system administrators can curate the shared regulatory knowledge base")
    if (file.content_type or "").lower() != "application/pdf" or not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF regulatory sources are accepted")
    title = source_title.strip()
    if not title or len(title) > 255:
        raise HTTPException(status_code=400, detail="Source title must be between 1 and 255 characters")
    if source_url and (len(source_url) > 1000 or not source_url.startswith(("https://", "http://"))):
        raise HTTPException(status_code=400, detail="Source URL must be an http(s) URL no longer than 1000 characters")
    content = await file.read(settings.MAX_FILE_SIZE_BYTES + 1)
    if len(content) > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"Regulatory PDF exceeds the configured {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit")
    if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-2048:]:
        raise HTTPException(status_code=400, detail="The uploaded file does not appear to be a complete PDF")
    try:
        extracted = extract_pdf_pages(content)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if not extracted["has_extractable_text"]:
        raise HTTPException(status_code=422, detail="No readable text was extracted. Install/configure OCR or upload a searchable PDF.")
    digest = sha256_bytes(content)
    existing = db.query(RegulatoryChunk).filter(RegulatoryChunk.content_sha256 == digest, RegulatoryChunk.is_active.is_(True)).first()
    if existing:
        raise HTTPException(status_code=409, detail="This exact PDF is already indexed in the active knowledge base")
    chunk_items = []
    # Keep chunks page-aware so answer citations can point back to the source PDF.
    for page in extracted["pages"]:
        page_text = (page["text"] or "").strip()
        if not page_text:
            continue
        paragraphs = re.split(r"\n\s*\n", page_text)
        buffer = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if len(buffer) + len(paragraph) > 1400 and buffer:
                chunk_items.append({"page": page["page"], "text": buffer[:1600]})
                buffer = ""
            buffer = (buffer + "\n\n" + paragraph).strip()
        if buffer:
            chunk_items.append({"page": page["page"], "text": buffer[:1600]})
    # Bound corpus growth from unexpectedly repetitive or very dense PDFs.
    chunk_items = chunk_items[:500]
    added = len(chunk_items)
    if added:
        vectors = []
        for offset in range(0, added, 32):
            batch = _ollama_embed([item["text"] for item in chunk_items[offset:offset + 32]])
            if batch is None:
                vectors = []
                break
            vectors.extend(batch)
        for index, item in enumerate(chunk_items):
            db.add(RegulatoryChunk(source_title=title, source_url=source_url,
                source_version=(source_version or "").strip()[:100] or None,
                page_number=item["page"], chunk_text=item["text"],
                embedding_json=vectors[index] if len(vectors) == added else None,
                content_sha256=digest, is_active=True, uploaded_by_user_id=current_user.id))
    if not added:
        raise HTTPException(status_code=422, detail="No indexable text chunks were found")
    AuditService.record_system_event(db, current_user, "REGULATORY_SOURCE_INDEXED", "RegulatorySource", digest,
        {"source_title": title, "source_version": source_version, "chunks_added": added})
    db.commit()
    return {"source_title": title, "source_version": source_version, "chunks_added": added, "page_count": extracted["page_count"], "content_sha256": digest, "status": "indexed"}


@router.get("/knowledge")
def list_regulatory_sources(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Source catalogue only: no private uploaded application content is exposed here.
    rows = db.query(RegulatoryChunk).filter(RegulatoryChunk.is_active.is_(True)).all()
    grouped = {}
    for row in rows:
        key = row.content_sha256
        if key not in grouped:
            grouped[key] = {"source_title": row.source_title, "source_url": row.source_url, "source_version": row.source_version,
                            "content_sha256": key, "chunks": 0, "pages": set(), "created_at": row.created_at.isoformat() if row.created_at else None}
        grouped[key]["chunks"] += 1
        if row.page_number:
            grouped[key]["pages"].add(row.page_number)
    return [{**value, "pages": len(value["pages"])} for value in grouped.values()]


@router.post("/ask")
def ask_regulatory_question(payload: AskRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    question = payload.question.strip()
    if len(question) < 3:
        raise HTTPException(status_code=422, detail="Enter a more specific question")
    chunks = retrieve_chunks(db, question, limit=5)
    result = answer_question(question, chunks)
    result["disclaimer"] = "Advisory information only. Verify the cited official source and applicable version. This assistant cannot approve, reject or advance an application."
    return result


@router.post("/knowledge/{content_sha256}/deactivate")
def deactivate_regulatory_source(content_sha256: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "SYSTEM_ADMIN":
        raise HTTPException(status_code=403, detail="Only system administrators can deactivate regulatory sources")
    if not re.fullmatch(r"[a-f0-9]{64}", content_sha256):
        raise HTTPException(status_code=400, detail="Invalid source fingerprint")
    rows = db.query(RegulatoryChunk).filter(RegulatoryChunk.content_sha256 == content_sha256, RegulatoryChunk.is_active.is_(True)).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Active regulatory source not found")
    for row in rows:
        row.is_active = False
    AuditService.record_system_event(db, current_user, "REGULATORY_SOURCE_DEACTIVATED", "RegulatorySource", content_sha256,
        {"source_title": rows[0].source_title, "chunks_deactivated": len(rows)})
    db.commit()
    return {"status": "deactivated", "source_title": rows[0].source_title, "chunks_deactivated": len(rows)}
