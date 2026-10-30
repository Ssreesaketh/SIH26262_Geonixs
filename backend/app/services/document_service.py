import os
import re
import uuid
from datetime import datetime, timezone, date
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.entities import Document

# Deliberately allow only formats that can be safely served as downloads.
ALLOWED_MIME_TYPES = {
    "application/pdf": (".pdf", {b"%PDF-"}),
    "image/jpeg": (".jpg", {b"\xff\xd8\xff"}),
    "image/png": (".png", {b"\x89PNG\r\n\x1a\n"}),
}
ALLOWED_DOCUMENT_TYPES = {
    "LAND_LEASE_DEED", "FIRE_NOC", "BUILDING_STABILITY_CERT",
    "AICTE_AFFIDAVIT", "UNDERTAKING_EVIDENCE", "INSTITUTION_INFORMATION_FORM",
    "APPLICATION_SUPPORTING_DOCUMENT", "OTHER_REGULATORY_DOCUMENT",
}
CHUNK_SIZE = 1024 * 1024


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DocumentService:
    @staticmethod
    async def save_upload(
        db: Session,
        file: UploadFile,
        institution_id: str,
        document_type: str,
        display_name: Optional[str] = None,
        expiry_date: Optional[date] = None,
        application_id: Optional[str] = None,
        undertaking_id: Optional[str] = None,
        renewal_of_id: Optional[str] = None,
    ) -> Document:
        if document_type not in ALLOWED_DOCUMENT_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported document type.")

        content_type = (file.content_type or "").lower().strip()
        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail="Unsupported file type. Upload PDF, JPEG, or PNG only.")

        original_name = (file.filename or "document").replace("\\", "/").split("/")[-1]
        if not original_name or len(original_name) > 255 or any(ord(c) < 32 for c in original_name):
            raise HTTPException(status_code=400, detail="Invalid filename.")
        expected_ext = ALLOWED_MIME_TYPES[content_type][0]
        if os.path.splitext(original_name)[1].lower() not in ({".jpg", ".jpeg"} if content_type == "image/jpeg" else {expected_ext}):
            raise HTTPException(status_code=400, detail="File extension does not match the permitted file content type.")

        # Read in bounded chunks. Never accept an unbounded request body into memory.
        max_bytes = max(1, int(settings.MAX_FILE_SIZE_BYTES))
        chunks = []
        total = 0
        while True:
            chunk = await file.read(min(CHUNK_SIZE, max_bytes + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise HTTPException(status_code=413, detail=f"File exceeds the {max_bytes // (1024 * 1024)} MB upload limit.")
            chunks.append(chunk)
        content = b"".join(chunks)
        if not content:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        # Verify the bytes, not only the browser-supplied MIME type.
        if not any(content.startswith(sig) for sig in ALLOWED_MIME_TYPES[content_type][1]):
            raise HTTPException(status_code=400, detail="File content does not match the declared PDF/JPEG/PNG type.")
        if content_type == "application/pdf" and (b"%%EOF" not in content[-2048:]):
            raise HTTPException(status_code=400, detail="The PDF appears incomplete or invalid.")
        if content_type == "image/png" and b"IEND" not in content[-32:]:
            raise HTTPException(status_code=400, detail="The PNG appears incomplete or invalid.")
        if content_type == "image/jpeg" and not content.rstrip().endswith(b"\xff\xd9"):
            raise HTTPException(status_code=400, detail="The JPEG appears incomplete or invalid.")

        storage_root = os.path.realpath(settings.STORAGE_DIR)
        os.makedirs(storage_root, mode=0o750, exist_ok=True)
        storage_key = f"{uuid.uuid4().hex}{expected_ext}"
        storage_path = os.path.realpath(os.path.join(storage_root, storage_key))
        if os.path.commonpath([storage_root, storage_path]) != storage_root:
            raise HTTPException(status_code=400, detail="Invalid storage path.")

        # Exclusive create avoids overwriting any existing file, even in a collision.
        try:
            with open(storage_path, "xb") as out:
                out.write(content)
        except FileExistsError:
            raise HTTPException(status_code=500, detail="Could not allocate secure document storage.")

        if renewal_of_id:
            old_doc = db.query(Document).filter(Document.id == renewal_of_id).first()
            if not old_doc:
                os.remove(storage_path)
                raise HTTPException(status_code=404, detail="Document being renewed was not found.")
            if old_doc.institution_id != institution_id:
                os.remove(storage_path)
                raise HTTPException(status_code=403, detail="A document can only be renewed within the same institution.")
            if old_doc.status not in {"RETURNED_FOR_CORRECTION", "EXPIRED", "EXPIRING_SOON", "VALID"}:
                os.remove(storage_path)
                raise HTTPException(status_code=409, detail="Only a returned, expired, expiring, or legacy-valid document can be replaced.")
            if old_doc.document_type != document_type:
                os.remove(storage_path)
                raise HTTPException(status_code=400, detail="A replacement must keep the original document type.")
            old_doc.status = "SUPERSEDED"

        safe_display_name = re.sub(r"[\x00-\x1f\x7f]", "", (display_name or original_name)).strip()
        safe_display_name = safe_display_name[:255] or "Document"
        doc = Document(
            application_id=application_id,
            institution_id=institution_id,
            undertaking_id=undertaking_id,
            document_type=document_type,
            display_name=safe_display_name,
            storage_key=storage_key,
            mime_type=content_type,
            file_size=total,
            expiry_date=expiry_date,
            status="SUBMITTED",
            renewal_of_id=renewal_of_id,
            submitted_at=utc_now(),
            verified_by=None,
            verified_at=None,
            verification_remarks=None,
        )
        db.add(doc)
        db.flush()
        db.refresh(doc)
        return doc

    @staticmethod
    def get_file_path(document: Document) -> str:
        storage_root = os.path.realpath(settings.STORAGE_DIR)
        storage_path = os.path.realpath(os.path.join(storage_root, document.storage_key))
        if os.path.commonpath([storage_root, storage_path]) != storage_root:
            raise HTTPException(status_code=400, detail="Invalid storage path.")
        if not os.path.isfile(storage_path):
            raise HTTPException(status_code=404, detail="File content not found on server storage.")
        return storage_path
