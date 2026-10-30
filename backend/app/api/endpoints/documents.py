from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date
from pathlib import Path
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.auth import get_current_user, verify_institution_access, verify_regional_access
from app.models.entities import Document, Institution, Application, Undertaking, User
from app.schemas.domain import DocumentResponse
from app.services.document_service import DocumentService, ALLOWED_DOCUMENT_TYPES
from app.services.audit_service import AuditService

router = APIRouter()


FORM_CATALOG = {
    "institution-application-checklist": {
        "title": "Institution application checklist",
        "description": "Pre-submission checklist for an institution's application.",
        "filename": "institution-application-checklist.pdf",
        "roles": {"INSTITUTION_USER", "REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"},
        "audience": "institution",
    },
    "institution-information-form": {
        "title": "Institution information form",
        "description": "Working template for institution profile and programme details.",
        "filename": "institution-information-form.pdf",
        "roles": {"INSTITUTION_USER", "REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"},
        "audience": "institution",
    },
    "evc-inspection-report": {
        "title": "EVC inspection report",
        "description": "Officer-only inspection findings and evidence template.",
        "filename": "evc-inspection-report.pdf",
        "roles": {"REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"},
        "audience": "officer",
    },
    "bureau-review-checklist": {
        "title": "Bureau review checklist",
        "description": "Officer-only review checklist for EVC findings and recommendations.",
        "filename": "bureau-review-checklist.pdf",
        "roles": {"BUREAU_OFFICER", "SYSTEM_ADMIN"},
        "audience": "officer",
    },
}

@router.get("/forms")
def list_downloadable_forms(current_user: User = Depends(get_current_user)):
    """Return only templates available to the authenticated role."""
    return [
        {
            "key": key,
            "title": item["title"],
            "description": item["description"],
            "filename": item["filename"],
            "audience": item["audience"],
            "download_url": f"/api/v1/documents/forms/{key}/download",
        }
        for key, item in FORM_CATALOG.items()
        if current_user.role in item["roles"]
    ]

@router.get("/forms/{form_key}/download")
def download_form(form_key: str, current_user: User = Depends(get_current_user)):
    item = FORM_CATALOG.get(form_key)
    if not item:
        raise HTTPException(status_code=404, detail="Form template not found")
    if current_user.role not in item["roles"]:
        raise HTTPException(status_code=403, detail="This form is not available to your role")
    form_path = Path(__file__).resolve().parents[2] / "static" / "forms" / item["filename"]
    if not form_path.is_file():
        raise HTTPException(status_code=404, detail="Form template file is not installed")
    return FileResponse(
        path=str(form_path),
        media_type="application/pdf",
        filename=item["filename"],
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff", "Content-Security-Policy": "default-src 'none'"},
    )

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@router.get("", response_model=List[DocumentResponse])
def list_documents(
    status_filter: Optional[str] = None,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Document).join(Institution)

    if current_user.role == "INSTITUTION_USER":
        query = query.filter(Document.institution_id == current_user.institution_id)
    elif current_user.role == "REGIONAL_OFFICER":
        if not current_user.region_id:
            raise HTTPException(status_code=403, detail="Regional officer account has no region assignment")
        query = query.filter(Institution.region_id == current_user.region_id)
    # Bureau/System Admin see the shared registry; regional officers are region-scoped.
    if status_filter:
        query = query.filter(Document.status == status_filter)
    if document_type:
        query = query.filter(Document.document_type == document_type)

    return query.order_by(Document.expiry_date.asc().nullslast()).all()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    display_name: Optional[str] = Form(None),
    expiry_date_str: Optional[str] = Form(None),
    institution_id: Optional[str] = Form(None),
    application_id: Optional[str] = Form(None),
    undertaking_id: Optional[str] = Form(None),
    renewal_of_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "INSTITUTION_USER":
        raise HTTPException(
            status_code=403,
            detail="Only institution users may upload their institution's documents",
        )

    # Institution tenant is authoritative; never trust a client-selected tenant.
    target_inst_id = current_user.institution_id
    if institution_id and institution_id != target_inst_id:
        raise HTTPException(status_code=403, detail="You can only upload documents for your own institution")
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported document type")
    if not target_inst_id:
        raise HTTPException(status_code=400, detail="institution_id must be provided")

    target_inst = db.query(Institution).filter(Institution.id == target_inst_id).first()
    if not target_inst:
        raise HTTPException(status_code=404, detail="Target institution not found")
    verify_institution_access(current_user, target_inst_id)
    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, target_inst.region_id)

    # Ensure optional links belong to the same authorized institution/case.
    linked_app = None
    if application_id:
        linked_app = db.query(Application).filter(Application.id == application_id).first()
        if not linked_app:
            raise HTTPException(status_code=404, detail="Application not found")
        if linked_app.institution_id != target_inst_id:
            raise HTTPException(status_code=403, detail="Application does not belong to the target institution")
        if current_user.role == "REGIONAL_OFFICER":
            verify_regional_access(current_user, linked_app.institution.region_id)
    if undertaking_id:
        linked_undertaking = db.query(Undertaking).filter(Undertaking.id == undertaking_id).first()
        if not linked_undertaking:
            raise HTTPException(status_code=404, detail="Undertaking not found")
        if linked_undertaking.institution_id != target_inst_id or (application_id and linked_undertaking.application_id != application_id):
            raise HTTPException(status_code=403, detail="Undertaking does not belong to the target institution/application")
        if application_id is None:
            application_id = linked_undertaking.application_id
    if renewal_of_id:
        old_doc = db.query(Document).filter(Document.id == renewal_of_id).first()
        if not old_doc:
            raise HTTPException(status_code=404, detail="Document being renewed was not found")
        if old_doc.institution_id != target_inst_id:
            raise HTTPException(status_code=403, detail="Document being renewed belongs to another institution")
        if old_doc.status != "RETURNED_FOR_CORRECTION":
            raise HTTPException(status_code=409, detail="Only a document returned for correction can be resubmitted through the upload form")
        if old_doc.document_type != document_type:
            raise HTTPException(status_code=400, detail="A replacement must keep the original document type")

    parsed_expiry: Optional[date] = None
    if expiry_date_str and expiry_date_str.strip():
        try:
            parsed_expiry = datetime.strptime(expiry_date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid expiry date format. Expected YYYY-MM-DD.")

    doc = await DocumentService.save_upload(
        db=db,
        file=file,
        institution_id=target_inst_id,
        document_type=document_type,
        display_name=display_name or file.filename,
        expiry_date=parsed_expiry,
        application_id=application_id,
        undertaking_id=undertaking_id,
        renewal_of_id=renewal_of_id
    )

    if application_id:
        AuditService.record_event(db=db, application_id=application_id, actor=current_user,
            action="UPLOAD_DOCUMENT", reason=f"Uploaded {document_type}: {doc.display_name}")
    else:
        AuditService.record_system_event(db, current_user, "UPLOAD_DOCUMENT", "Document", doc.id,
            {"institution_id": target_inst_id, "document_type": document_type, "display_name": doc.display_name})
    db.commit()
    db.refresh(doc)
    return doc

@router.get("/{id}/download")
def download_document(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    verify_institution_access(current_user, doc.institution_id)
    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, doc.institution.region_id)

    file_path = DocumentService.get_file_path(doc)
    return FileResponse(
        path=file_path,
        media_type=doc.mime_type,
        filename=Path(file_path).name,
        headers={"Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff", "Content-Disposition": f'attachment; filename="{Path(file_path).name}"'},
    )

@router.post("/{id}/renew", response_model=DocumentResponse)
async def renew_document(
    id: str,
    file: UploadFile = File(...),
    new_expiry_date: str = Form(...),
    display_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "INSTITUTION_USER":
        raise HTTPException(status_code=403, detail="Only institution users may renew their institution's documents")
    old_doc = db.query(Document).filter(Document.id == id).first()
    if not old_doc:
        raise HTTPException(status_code=404, detail="Document to renew not found")

    verify_institution_access(current_user, old_doc.institution_id)
    if old_doc.status not in {"EXPIRED", "EXPIRING_SOON"}:
        raise HTTPException(status_code=409, detail="Only expired or expiring documents can use the renewal action")

    try:
        parsed_expiry = datetime.strptime(new_expiry_date.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid new_expiry_date format. Expected YYYY-MM-DD.")

    new_doc = await DocumentService.save_upload(
        db=db,
        file=file,
        institution_id=old_doc.institution_id,
        document_type=old_doc.document_type,
        display_name=display_name or f"Renewed {old_doc.display_name}",
        expiry_date=parsed_expiry,
        application_id=old_doc.application_id,
        renewal_of_id=old_doc.id
    )

    if old_doc.application_id:
        AuditService.record_event(db=db, application_id=old_doc.application_id, actor=current_user,
            action="RENEW_DOCUMENT", reason=f"Renewed document {old_doc.display_name}. New expiry: {parsed_expiry}.")
    else:
        AuditService.record_system_event(db, current_user, "RENEW_DOCUMENT", "Document", new_doc.id,
            {"renewal_of_id": old_doc.id, "new_expiry": parsed_expiry.isoformat()})
    db.commit()
    db.refresh(new_doc)
    return new_doc


class DocumentReviewRequest(BaseModel):
    status: Literal["VERIFIED", "RETURNED_FOR_CORRECTION"]
    remarks: str = Field(min_length=3, max_length=1000)


@router.post("/{id}/review", response_model=DocumentResponse)
def review_document(
    id: str,
    payload: DocumentReviewRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in {"REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"}:
        raise HTTPException(status_code=403, detail="Only authorized officers can review submitted documents")
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, doc.institution.region_id if doc.institution else None)
    if doc.status not in {"SUBMITTED", "RETURNED_FOR_CORRECTION"}:
        raise HTTPException(status_code=409, detail=f"A document in status {doc.status} cannot be reviewed")
    doc.status = payload.status
    doc.verified_by = current_user.id
    doc.verified_at = utc_now()
    doc.verification_remarks = payload.remarks.strip()
    if doc.application_id:
        AuditService.record_event(
            db=db, application_id=doc.application_id, actor=current_user,
            action="DOCUMENT_" + payload.status,
            reason=doc.verification_remarks,
        )
    else:
        AuditService.record_system_event(
            db, current_user, "DOCUMENT_" + payload.status, "Document", doc.id,
            {"institution_id": doc.institution_id, "remarks": doc.verification_remarks},
        )
    db.commit()
    db.refresh(doc)
    return doc
