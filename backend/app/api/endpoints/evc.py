from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles, verify_regional_access
from app.models.entities import EVCEvent, Application, Institution, User
from app.schemas.domain import EVCScheduleRequest, EVCCompleteRequest, EVCEventResponse
from app.services.audit_service import AuditService

router = APIRouter()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@router.get("", response_model=List[EVCEventResponse])
def list_evc_events(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(EVCEvent).join(Application).join(Institution)

    if current_user.role == "INSTITUTION_USER":
        if not current_user.institution_id:
            raise HTTPException(status_code=403, detail="Institution user account has no institution assignment")
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif current_user.role == "REGIONAL_OFFICER":
        if not current_user.region_id:
            raise HTTPException(status_code=403, detail="Regional officer account has no region assignment")
        query = query.filter(Institution.region_id == current_user.region_id)
    # Bureau/admin users see the shared operational schedule; institution users
    # and regional officers are scoped to their own authorized records.
    if status_filter:
        query = query.filter(EVCEvent.status == status_filter)

    events = query.order_by(EVCEvent.scheduling_deadline.asc()).all()
    responses = [EVCEventResponse.model_validate(event) for event in events]
    if current_user.role == "INSTITUTION_USER":
        for response in responses:
            details = response.committee_details or {}
            response.committee_details = {
                key: details[key]
                for key in ("recommended_mode", "venue")
                if key in details
            }
    return responses

@router.post("/applications/{application_id}", response_model=EVCEventResponse)
def schedule_evc(
    application_id: str,
    payload: EVCScheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]))
):
    app = db.query(Application).filter(Application.id == application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if current_user.role not in {"REGIONAL_OFFICER", "SYSTEM_ADMIN"}:
        raise HTTPException(status_code=403, detail="Only the Regional Officer may schedule EVC inspections")
    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, app.institution.region_id)
    if app.current_stage_code != "EVC" or app.workflow_status in {"STAGE_COMPLETED", "COMPLETED"}:
        raise HTTPException(status_code=409, detail="EVC can only be scheduled for an active application in the EVC stage")

    # Check if existing EVC record exists
    evc = db.query(EVCEvent).filter(EVCEvent.application_id == application_id).first()
    now = utc_now()
    scheduled_date = payload.scheduled_date
    if scheduled_date.tzinfo is None:
        scheduled_date = scheduled_date.replace(tzinfo=timezone.utc)
    if scheduled_date <= now:
        raise HTTPException(status_code=422, detail="Inspection must be scheduled for a future date and time")
    if not evc:
        evc = EVCEvent(
            application_id=application_id,
            scheduling_deadline=now + timedelta(days=14)
        )
        db.add(evc)

    evc.status = "SCHEDULED"
    evc.scheduled_date = scheduled_date
    evc.committee_details = payload.committee_details
    
    app.workflow_status = "SCHEDULED"

    AuditService.record_event(
        db=db,
        application_id=app.id,
        actor=current_user,
        action="SCHEDULE_EVC",
        from_stage=app.current_stage_code,
        to_stage=app.current_stage_code,
        reason=f"EVC visit scheduled for {scheduled_date.strftime('%Y-%m-%d %H:%M UTC')}.",
        metadata_json=payload.committee_details
    )

    db.commit()
    db.refresh(evc)
    return evc

@router.post("/{id}/complete", response_model=EVCEventResponse)
def complete_evc(
    id: str,
    payload: EVCCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "SYSTEM_ADMIN"]))
):
    evc = db.query(EVCEvent).filter(EVCEvent.id == id).first()
    if not evc:
        raise HTTPException(status_code=404, detail="EVC event not found")

    app = evc.application
    if current_user.role not in {"REGIONAL_OFFICER", "SYSTEM_ADMIN"}:
        raise HTTPException(status_code=403, detail="Only the Regional Officer may submit EVC findings")
    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, app.institution.region_id)
    if app.current_stage_code != "EVC" or evc.status != "SCHEDULED":
        raise HTTPException(status_code=409, detail="Findings can only be submitted for a scheduled inspection in the EVC stage")
    if not payload.findings_summary or not payload.findings_summary.strip():
        raise HTTPException(status_code=422, detail="Inspection findings are required")
    outcome = (payload.outcome or "RECOMMENDED").strip().upper()
    if outcome not in {"RECOMMENDED", "DEFICIENT"}:
        raise HTTPException(status_code=422, detail="Outcome must be RECOMMENDED or DEFICIENT")

    now = utc_now()
    from_stage = app.current_stage_code
    evc.status = "FINDINGS_SUBMITTED"
    evc.findings_summary = payload.findings_summary.strip()
    evc.completed_at = now

    if outcome == "RECOMMENDED":
        app.current_stage_code = "SAC_SHC"
        app.workflow_status = "UNDER_REVIEW"
        app.assigned_role = "BUREAU_OFFICER"
        app.stage_entered_at = now
        app.stage_due_at = now + timedelta(days=10)
        to_stage = "SAC_SHC"
        event_reason = "EVC inspection completed; findings recommend bureau review. " + payload.findings_summary.strip()
    else:
        app.workflow_status = "DEFICIENCY_RETURNED"
        app.assigned_role = "INSTITUTION_USER"
        app.stage_entered_at = now
        app.stage_due_at = now + timedelta(days=10)
        to_stage = "EVC"
        event_reason = "EVC inspection returned for institutional deficiencies. " + payload.findings_summary.strip()

    AuditService.record_event(
        db=db,
        application_id=app.id,
        actor=current_user,
        action="EVC_FINDINGS_SUBMITTED",
        from_stage=from_stage,
        to_stage=to_stage,
        reason=event_reason,
        metadata_json={"outcome": outcome}
    )

    db.commit()
    db.refresh(evc)
    return evc
