from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
from app.core.database import get_db
from app.core.auth import get_current_user, require_roles
from app.models.entities import Notification, Application, Document, Undertaking, Institution, User
from app.schemas.domain import NotificationResponse, AlertCheckResponse, NotificationAcknowledgeRequest
from app.services.sla_engine import SLAEngine
from app.services.audit_service import AuditService

router = APIRouter()

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def _visible_to_user(db: Session, notif: Notification, user: User) -> bool:
    if user.role == "SYSTEM_ADMIN":
        return True
    app = db.query(Application).filter(Application.id == notif.application_id).first() if notif.application_id else None
    document = db.query(Document).filter(Document.id == notif.document_id).first() if notif.document_id else None
    undertaking = db.query(Undertaking).filter(Undertaking.id == notif.undertaking_id).first() if notif.undertaking_id else None
    institution_id = (app.institution_id if app else None) or (document.institution_id if document else None) or (undertaking.institution_id if undertaking else None)
    role_allowed = notif.recipient_role in {user.role, "ALL"}
    direct_recipient = notif.recipient_user_id == user.id
    if user.role == "INSTITUTION_USER":
        # A direct recipient assignment never overrides tenant isolation.
        return bool(user.institution_id and institution_id == user.institution_id and
                    (notif.recipient_role == "INSTITUTION_USER" or direct_recipient))
    if user.role == "REGIONAL_OFFICER":
        if not (role_allowed or direct_recipient) or not user.region_id:
            return False
        institution = db.query(Institution).filter(Institution.id == institution_id).first() if institution_id else None
        return bool(institution and institution.region_id == user.region_id)
    if user.role in {"BUREAU_OFFICER", "EVC_MEMBER"}:
        if not (role_allowed or direct_recipient):
            return False
        if user.role == "EVC_MEMBER":
            return bool(app and app.current_stage_code == "EVC")
        return bool(app or (document and document.institution_id) or (undertaking and undertaking.institution_id))
    return False

def _response(db: Session, notif: Notification) -> NotificationResponse:
    resp = NotificationResponse.model_validate(notif)
    if notif.application:
        resp.application_no = notif.application.application_no
    return resp

@router.get("", response_model=List[NotificationResponse])
def list_alerts(severity: Optional[str] = None, status_filter: Optional[str] = None,
                db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = db.query(Notification)
    if severity:
        query = query.filter(Notification.severity == severity)
    if status_filter:
        query = query.filter(Notification.status == status_filter)
    candidates = query.order_by(Notification.created_at.desc()).limit(500).all()
    return [_response(db, n) for n in candidates if _visible_to_user(db, n, current_user)][:100]

@router.post("/check", response_model=AlertCheckResponse)
def trigger_deadline_check(db: Session = Depends(get_db), current_user: User = Depends(require_roles(["REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"]))):
    total, new_created, details = SLAEngine.evaluate_all(db)
    return AlertCheckResponse(total_evaluated=total, new_alerts_created=new_created, checked_at=utc_now(), details=details)

@router.post("/{id}/acknowledge", response_model=NotificationResponse)
def acknowledge_alert(id: str, payload: Optional[NotificationAcknowledgeRequest] = None,
                      db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = db.query(Notification).filter(Notification.id == id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification alert not found")
    if not _visible_to_user(db, notif, current_user):
        raise HTTPException(status_code=403, detail="You are not authorized to acknowledge this alert")
    previous = notif.status
    notif.status, notif.acknowledged_at = "ACKNOWLEDGED", utc_now()
    AuditService.record_system_event(db, current_user, "ALERT_ACKNOWLEDGED", "Notification", notif.id, {"from_status": previous, "to_status": notif.status})
    db.commit(); db.refresh(notif)
    return _response(db, notif)

@router.post("/{id}/resolve", response_model=NotificationResponse)
def resolve_alert(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = db.query(Notification).filter(Notification.id == id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification alert not found")
    if not _visible_to_user(db, notif, current_user):
        raise HTTPException(status_code=403, detail="You are not authorized to resolve this alert")
    if current_user.role not in {"SYSTEM_ADMIN", "REGIONAL_OFFICER", "BUREAU_OFFICER"}:
        raise HTTPException(status_code=403, detail="Only operational officers can resolve alerts")
    previous = notif.status
    notif.status = "RESOLVED"
    AuditService.record_system_event(db, current_user, "ALERT_RESOLVED", "Notification", notif.id, {"from_status": previous, "to_status": notif.status})
    db.commit(); db.refresh(notif)
    return _response(db, notif)
