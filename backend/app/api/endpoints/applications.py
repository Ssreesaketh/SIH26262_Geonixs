import random
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from app.core.database import get_db
from app.core.auth import get_current_user, verify_institution_access, verify_regional_access
from app.models.entities import (
    Application, Institution, Region, WorkflowTemplate, ApplicationEvent, User
)
from app.schemas.domain import (
    ApplicationCreate, ApplicationActionRequest, ApplicationResponse,
    ApplicationDetailResponse, ApplicationListResponse, ApplicationEventResponse,
    InstitutionResponse
)
from app.services.workflow_engine import WorkflowEngine
from app.services.audit_service import AuditService

router = APIRouter()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

@router.get("", response_model=ApplicationListResponse)
def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    stage: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    region_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Application).join(Institution).join(Region)

    # Enforce tenant and regional scope in the list query itself. Object-level
    # checks on detail/action endpoints do not prevent registry-level disclosure.
    if current_user.role == "INSTITUTION_USER":
        if not current_user.institution_id:
            raise HTTPException(status_code=403, detail="Institution account has no institution assignment")
        query = query.filter(Application.institution_id == current_user.institution_id)
    elif current_user.role == "REGIONAL_OFFICER":
        if not current_user.region_id:
            raise HTTPException(status_code=403, detail="Regional officer account has no region assignment")
        query = query.filter(Institution.region_id == current_user.region_id)
        # Regional officers cannot broaden or switch their assigned region using a query parameter.
    elif current_user.role in {"BUREAU_OFFICER", "SYSTEM_ADMIN"}:
        if region_id:
            query = query.filter(Institution.region_id == region_id)
    else:
        raise HTTPException(status_code=403, detail="Role is not authorized to view the application registry")

    if stage:
        query = query.filter(Application.current_stage_code == stage)
    if status_filter:
        query = query.filter(Application.workflow_status == status_filter)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Application.application_no.ilike(search_pattern),
                Institution.name.ilike(search_pattern),
                Institution.institution_code.ilike(search_pattern)
            )
        )

    total = query.count()
    items = query.order_by(desc(Application.updated_at)).offset((page - 1) * page_size).limit(page_size).all()

    response_items = []
    for app in items:
        resp = ApplicationResponse.model_validate(app)
        resp.institution_name = app.institution.name if app.institution else None
        resp.region_code = app.institution.region.code if app.institution and app.institution.region else None
        if current_user.role == "INSTITUTION_USER":
            # Never disclose internal assignment or committee recommendations.
            resp.assigned_role = "UNDER_PROCESS"
            if app.workflow_status != "STAGE_COMPLETED":
                resp.decision_status = "NOT_DISCLOSED"
        response_items.append(resp)

    return ApplicationListResponse(
        items=response_items,
        total=total,
        page=page,
        page_size=page_size
    )

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only an institution account may create a draft, and its tenant is derived
    # from the authenticated identity rather than trusting a client-supplied ID.
    if current_user.role != "INSTITUTION_USER":
        raise HTTPException(status_code=403, detail="Only institution users can create application drafts")
    if not current_user.institution_id:
        raise HTTPException(status_code=403, detail="This institution account is not linked to an institution")
    if payload.institution_id != current_user.institution_id:
        raise HTTPException(status_code=403, detail="You can only create applications for your own institution")

    # Check institution exists
    inst = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found")

    # Load workflow template
    wf = db.query(WorkflowTemplate).filter(
        WorkflowTemplate.code == payload.workflow_template_code,
        WorkflowTemplate.is_active == True
    ).order_by(desc(WorkflowTemplate.version)).first()

    if not wf:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow template '{payload.workflow_template_code}' not found or inactive"
        )

    # Generate unique application_no
    year = datetime.now().year
    rand_seq = random.randint(1000, 9999)
    app_no = f"APP-{year}-AICTE-{rand_seq}"
    while db.query(Application).filter(Application.application_no == app_no).first():
        rand_seq = random.randint(1000, 9999)
        app_no = f"APP-{year}-AICTE-{rand_seq}"

    now = utc_now()
    due = now + timedelta(days=30) # Initial draft window

    application = Application(
        application_no=app_no,
        institution_id=payload.institution_id,
        application_type=payload.application_type,
        workflow_template_id=wf.id,
        workflow_version=wf.version,
        current_stage_code="DRAFT",
        workflow_status="DRAFT",
        decision_status="NOT_RECORDED",
        assigned_role="INSTITUTION_USER",
        stage_entered_at=now,
        stage_due_at=due,
        created_at=now,
        updated_at=now
    )
    db.add(application)
    db.flush()

    # Record audit event
    AuditService.record_event(
        db=db,
        application_id=application.id,
        actor=current_user,
        action="CREATE",
        from_stage=None,
        to_stage="DRAFT",
        reason="Initial application draft created."
    )
    db.commit()
    db.refresh(application)

    resp = ApplicationResponse.model_validate(application)
    resp.institution_name = inst.name
    resp.region_code = inst.region.code if inst.region else None
    return resp

@router.get("/{id}", response_model=ApplicationDetailResponse)
def get_application(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Enforce access scope
    verify_institution_access(current_user, app.institution_id)
    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, app.institution.region_id)

    permitted = WorkflowEngine.get_permitted_actions(app, current_user)
    
    resp = ApplicationDetailResponse.model_validate(app)
    resp.institution_name = app.institution.name if app.institution else None
    resp.region_code = app.institution.region.code if app.institution and app.institution.region else None
    resp.permitted_actions = permitted
    if current_user.role == "INSTITUTION_USER":
        resp.assigned_role = "UNDER_PROCESS"
        if app.workflow_status != "STAGE_COMPLETED":
            resp.decision_status = "NOT_DISCLOSED"
        # Share visit logistics with the institution, but not private committee
        # member details or other internal scheduling metadata.
        for evc in resp.evc_events:
            details = evc.committee_details or {}
            evc.committee_details = {
                key: details[key]
                for key in ("recommended_mode", "venue")
                if key in details
            }

    # Institution users receive a public-facing timeline only. Internal workflow
    # metadata, individual officer identities and internal actions are not exposed.
    if current_user.role == "INSTITUTION_USER":
        public_actions = {
            "CREATE", "SUBMIT", "RETURN_DEFICIENCY", "RESUBMIT",
            "SCHEDULE_EVC", "EVC_FINDINGS_SUBMITTED", "FINAL_DECISION"
        }
        resp.events = [
            event for event in resp.events if event.action in public_actions
        ]
        for event in resp.events:
            event.actor_name = (
                "Institution representative"
                if event.actor_role == "INSTITUTION_USER"
                else "AICTE Officer"
            )
            event.actor_role = "INSTITUTION_USER" if event.actor_role == "INSTITUTION_USER" else "OFFICER"
            event.metadata_json = None
    else:
        for ev in resp.events:
            user_record = db.query(User).filter(User.id == ev.actor_user_id).first()
            if user_record:
                ev.actor_name = f"{user_record.display_name} ({user_record.role})"

    return resp

@router.post("/{id}/submit", response_model=ApplicationDetailResponse)
def submit_application(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(current_user, app.institution_id)
    WorkflowEngine.execute_transition(db=db, application=app, actor=current_user, action="SUBMIT")
    db.commit()
    db.refresh(app)

    return get_application(id=app.id, db=db, current_user=current_user)

@router.post("/{id}/actions", response_model=ApplicationDetailResponse)
def execute_application_action(
    id: str,
    payload: ApplicationActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(current_user, app.institution_id)
    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, app.institution.region_id)

    WorkflowEngine.execute_transition(
        db=db,
        application=app,
        actor=current_user,
        action=payload.action,
        reason=payload.reason,
        target_stage=payload.target_stage,
        decision_status=payload.decision_status
    )
    db.commit()
    db.refresh(app)

    return get_application(id=app.id, db=db, current_user=current_user)

@router.get("/{id}/history", response_model=List[ApplicationEventResponse])
def get_application_history(
    id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(Application.id == id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    verify_institution_access(current_user, app.institution_id)
    if current_user.role == "REGIONAL_OFFICER":
        verify_regional_access(current_user, app.institution.region_id)

    events = db.query(ApplicationEvent).filter(
        ApplicationEvent.application_id == id
    ).order_by(ApplicationEvent.created_at.asc()).all()
    if current_user.role == "INSTITUTION_USER":
        public_actions = {
            "CREATE", "SUBMIT", "RETURN_DEFICIENCY", "RESUBMIT",
            "SCHEDULE_EVC", "EVC_FINDINGS_SUBMITTED", "FINAL_DECISION"
        }
        events = [event for event in events if event.action in public_actions]

    res = []
    for ev in events:
        item = ApplicationEventResponse.model_validate(ev)
        if current_user.role == "INSTITUTION_USER":
            item.actor_name = "Institution representative" if ev.actor_role == "INSTITUTION_USER" else "AICTE Officer"
            item.actor_role = "INSTITUTION_USER" if ev.actor_role == "INSTITUTION_USER" else "OFFICER"
            item.metadata_json = None
        else:
            item.actor_name = f"{ev.actor.display_name} ({ev.actor.role})" if ev.actor else ev.actor_role
        res.append(item)
    return res
