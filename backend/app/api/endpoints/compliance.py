from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import get_current_user, verify_institution_access, verify_regional_access, require_roles
from app.models.entities import Undertaking, Application, Institution, User
from app.schemas.domain import (
    UndertakingCreate, UndertakingSubmitRequest, UndertakingVerifyRequest, UndertakingResponse
)
from app.services.audit_service import AuditService

router = APIRouter()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@router.get("", response_model=List[UndertakingResponse])
def list_undertakings(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Undertaking).join(Institution)

    if current_user.role == "INSTITUTION_USER":
        query = query.filter(Undertaking.institution_id == current_user.institution_id)
    elif current_user.role == "REGIONAL_OFFICER":
        if not current_user.region_id:
            raise HTTPException(status_code=403, detail="Regional officer account has no region assignment")
        query = query.filter(Institution.region_id == current_user.region_id)
    # Bureau/System Admin share the common view; regional officers see their region only.
    if status_filter:
        query = query.filter(Undertaking.status == status_filter)

    return query.order_by(Undertaking.due_at.asc()).all()

@router.post("/applications/{application_id}", response_model=UndertakingResponse)
def create_undertaking(
    application_id: str,
    payload: UndertakingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]))
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, app.institution.region_id)

    und = Undertaking(
        application_id=app.id,
        institution_id=app.institution_id,
        title=payload.title,
        description=payload.description,
        due_at=payload.due_at,
        status="PENDING"
    )
    db.add(und)
    db.flush()

    AuditService.record_event(
        db=db,
        application_id=app.id,
        actor=current_user,
        action="CREATE_UNDERTAKING",
        from_stage=app.current_stage_code,
        to_stage=app.current_stage_code,
        reason=f"Time-bound undertaking created: '{payload.title}'. Due on {payload.due_at.strftime('%Y-%m-%d')}."
    )

    db.commit()
    db.refresh(und)
    return und

@router.post("/{id}/submit", response_model=UndertakingResponse)
def submit_undertaking_evidence(
    id: str,
    payload: UndertakingSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    und = db.query(Undertaking).filter(Undertaking.id == id).first()
    if not und:
        raise HTTPException(status_code=404, detail="Undertaking not found")

    verify_institution_access(current_user, und.institution_id)

    und.status = "SUBMITTED"
    und.submitted_at = utc_now()
    und.evidence_summary = payload.evidence_summary

    AuditService.record_event(
        db=db,
        application_id=und.application_id,
        actor=current_user,
        action="SUBMIT_UNDERTAKING_EVIDENCE",
        from_stage=und.application.current_stage_code,
        to_stage=und.application.current_stage_code,
        reason=payload.evidence_summary
    )

    db.commit()
    db.refresh(und)
    return und

@router.post("/{id}/verify", response_model=UndertakingResponse)
def verify_undertaking(
    id: str,
    payload: UndertakingVerifyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]))
):
    und = db.query(Undertaking).filter(Undertaking.id == id).first()
    if not und:
        raise HTTPException(status_code=404, detail="Undertaking not found")

    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, und.institution.region_id)

    if payload.approved:
        und.status = "VERIFIED"
    else:
        und.status = "RETURNED_FOR_CORRECTION"

    und.verified_by = current_user.id
    und.verified_at = utc_now()
    und.verification_remarks = payload.verification_remarks

    AuditService.record_event(
        db=db,
        application_id=und.application_id,
        actor=current_user,
        action="VERIFY_UNDERTAKING" if payload.approved else "REJECT_UNDERTAKING_EVIDENCE",
        from_stage=und.application.current_stage_code,
        to_stage=und.application.current_stage_code,
        reason=payload.verification_remarks,
        metadata_json={"approved": payload.approved}
    )

    db.commit()
    db.refresh(und)
    return und
