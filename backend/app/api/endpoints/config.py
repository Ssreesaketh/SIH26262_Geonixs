from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.models.entities import WorkflowTemplate, User
from app.schemas.domain import WorkflowTemplateResponse, WorkflowTemplateUpdate
from app.services.audit_service import AuditService

router = APIRouter()
ALLOWED_ROLES = {"INSTITUTION_USER", "REGIONAL_OFFICER", "BUREAU_OFFICER", "EVC_MEMBER", "SYSTEM_ADMIN"}


def validate_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(config, dict):
        raise HTTPException(status_code=422, detail="configuration must be a JSON object")
    allowed_stages = {"DRAFT", "SCRUTINY", "EVC", "SAC_SHC", "COMPLETED"}
    stages = config.get("ordered_stages")
    slas = config.get("stage_slas")
    if not isinstance(stages, list) or not stages or not all(isinstance(x, str) and x.strip() for x in stages):
        raise HTTPException(status_code=422, detail="ordered_stages must be a non-empty list of stage codes")
    stages = [x.strip().upper() for x in stages]
    if any(stage not in allowed_stages for stage in stages):
        raise HTTPException(status_code=422, detail=f"ordered_stages may only contain: {', '.join(sorted(allowed_stages))}")
    if len(set(stages)) != len(stages):
        raise HTTPException(status_code=422, detail="ordered_stages cannot contain duplicates")
    if stages[0] == "DRAFT" or "DRAFT" in stages:
        raise HTTPException(status_code=422, detail="DRAFT is the pre-submission state and cannot be part of the post-submission route")
    if stages[-1] != "COMPLETED":
        raise HTTPException(status_code=422, detail="COMPLETED must be the final configured stage")
    if not isinstance(slas, dict):
        raise HTTPException(status_code=422, detail="stage_slas must be an object mapping stage codes to days")
    normalized_slas = {str(key).strip().upper(): value for key, value in slas.items()}
    for stage in stages:
        value = normalized_slas.get(stage)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise HTTPException(status_code=422, detail=f"stage_slas must contain a non-negative integer duration for {stage}")
    threshold = config.get("warning_threshold_percent", 80)
    if not isinstance(threshold, int) or isinstance(threshold, bool) or not 1 <= threshold <= 99:
        raise HTTPException(status_code=422, detail="warning_threshold_percent must be an integer from 1 to 99")
    windows = config.get("reminder_windows_hours", [48, 24])
    if not isinstance(windows, list) or any(not isinstance(x, int) or isinstance(x, bool) or x < 0 for x in windows):
        raise HTTPException(status_code=422, detail="reminder_windows_hours must be a list of non-negative integers")
    ladder = config.get("escalation_ladder", [
        {"after_days": 0, "recipient_role": "REGIONAL_OFFICER"},
        {"after_days": 3, "recipient_role": "BUREAU_OFFICER"},
        {"after_days": 7, "recipient_role": "SYSTEM_ADMIN"},
    ])
    if not isinstance(ladder, list) or not ladder:
        raise HTTPException(status_code=422, detail="escalation_ladder must be a non-empty list")
    normalized_ladder = []
    for item in ladder:
        if not isinstance(item, dict) or not isinstance(item.get("after_days"), int) or isinstance(item.get("after_days"), bool) or item["after_days"] < 0:
            raise HTTPException(status_code=422, detail="each escalation level needs a non-negative integer after_days")
        role = str(item.get("recipient_role", "")).upper()
        if role not in ALLOWED_ROLES:
            raise HTTPException(status_code=422, detail=f"unsupported escalation recipient_role: {role}")
        normalized_ladder.append({"after_days": item["after_days"], "recipient_role": role})
    normalized_ladder.sort(key=lambda x: x["after_days"])
    if normalized_ladder[0]["after_days"] != 0 or len({x["after_days"] for x in normalized_ladder}) != len(normalized_ladder):
        raise HTTPException(status_code=422, detail="escalation_ladder must start at day 0 and have unique after_days values")
    warning_role = str(config.get("warning_recipient_role", "REGIONAL_OFFICER")).upper()
    if warning_role not in ALLOWED_ROLES:
        raise HTTPException(status_code=422, detail=f"unsupported warning_recipient_role: {warning_role}")
    config["ordered_stages"] = stages
    config["stage_slas"] = normalized_slas
    config["warning_threshold_percent"] = threshold
    config["warning_recipient_role"] = warning_role
    config["reminder_windows_hours"] = sorted(set(windows), reverse=True)
    config["escalation_ladder"] = normalized_ladder
    return config

@router.get("/workflows", response_model=List[WorkflowTemplateResponse])
def list_workflow_templates(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(WorkflowTemplate).filter(WorkflowTemplate.is_active.is_(True)).order_by(WorkflowTemplate.code, desc(WorkflowTemplate.version)).all()


@router.get("/workflows/{code}/versions", response_model=List[WorkflowTemplateResponse])
def list_workflow_versions(code: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles(["SYSTEM_ADMIN"]))):
    rows = db.query(WorkflowTemplate).filter(WorkflowTemplate.code == code).order_by(desc(WorkflowTemplate.version)).all()
    return rows


@router.patch("/workflows/{id}", response_model=WorkflowTemplateResponse)
def update_workflow_template(id: str, payload: WorkflowTemplateUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(["SYSTEM_ADMIN"]))):
    wf = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == id, WorkflowTemplate.is_active.is_(True)).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Active workflow template not found")
    config = validate_configuration(dict(payload.configuration))
    latest_version = db.query(func.max(WorkflowTemplate.version)).filter(WorkflowTemplate.code == wf.code).scalar() or wf.version
    wf.is_active = False
    new_wf = WorkflowTemplate(code=wf.code, name=wf.name, version=latest_version + 1, configuration=config, is_active=True)
    db.add(new_wf)
    db.flush()
    AuditService.record_system_event(db, actor=current_user, action="WORKFLOW_RULE_VERSION_CREATED", target_type="WorkflowTemplate", target_id=new_wf.id, details={"code": new_wf.code, "version": new_wf.version, "configuration": config, "supersedes_version": wf.version})
    db.commit()
    db.refresh(new_wf)
    return new_wf


@router.get("/audit/verify")
def verify_audit_chain(db: Session = Depends(get_db), current_user: User = Depends(require_roles(["SYSTEM_ADMIN"]))):
    return AuditService.verify_chain(db)
