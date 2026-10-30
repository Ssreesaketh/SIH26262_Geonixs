from datetime import datetime, timezone, timedelta, date
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.entities import Application, EVCEvent, Undertaking, Document, Notification

DEFAULT_LADDER = [
    {"after_days": 0, "recipient_role": "REGIONAL_OFFICER"},
    {"after_days": 3, "recipient_role": "BUREAU_OFFICER"},
    {"after_days": 7, "recipient_role": "SYSTEM_ADMIN"},
]

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

class SLAEngine:
    @staticmethod
    def evaluate_all(db: Session) -> Tuple[int, int, List[str]]:
        """Evaluate deadline records idempotently; configured values are prototype rules, not official policy."""
        now, today = utc_now(), utc_now().date()
        evaluated, created_count, details = 0, 0, []

        active_apps = db.query(Application).filter(
            Application.current_stage_code != "COMPLETED",
            Application.workflow_status != "STAGE_COMPLETED"
        ).all()
        for app in active_apps:
            evaluated += 1
            due_at, entered_at = aware(app.stage_due_at), aware(app.stage_entered_at or app.created_at)
            config = (app.workflow_template.configuration or {}) if app.workflow_template else {}
            threshold = int(config.get("warning_threshold_percent", 80))
            duration = due_at - entered_at
            warning_at = entered_at + duration * (threshold / 100.0)
            stage_token = str(int(entered_at.timestamp()))
            if now >= due_at:
                overdue_days = max(0, (now - due_at).days)
                ladder = config.get("escalation_ladder") or DEFAULT_LADDER
                eligible = [level for level in ladder if overdue_days >= int(level.get("after_days", 0))]
                # Emit every newly reached level. Dedupe keys are scoped to this stage instance.
                for level_index, level in enumerate(eligible, start=1):
                    level_num = int(level.get("after_days", 0))
                    role = str(level.get("recipient_role", "REGIONAL_OFFICER"))
                    key = f"APP:{app.id}:STAGE:{app.current_stage_code}:{stage_token}:OVERDUE:D{level_num}"
                    made = SLAEngine._create_notification_if_absent(
                        db, key, "STAGE_SLA_BREACH", "CRITICAL",
                        f"Application {app.application_no} is overdue in {app.current_stage_code} by {overdue_days} day(s). Escalation level: day {level_num}.",
                        role, level_index, due_at, application_id=app.id)
                    if made:
                        created_count += 1
                        details.append(f"Created day-{level_num} overdue escalation for {app.application_no}")
            elif duration.total_seconds() > 0 and now >= warning_at:
                key = f"APP:{app.id}:STAGE:{app.current_stage_code}:{stage_token}:WARN:{threshold}"
                hours_left = max(0, int((due_at - now).total_seconds() // 3600))
                made = SLAEngine._create_notification_if_absent(
                    db, key, "STAGE_SLA_WARNING", "WARNING",
                    f"Application {app.application_no} has reached {threshold}% of its {app.current_stage_code} stage allowance; {hours_left} hour(s) remain.",
                    str(config.get("warning_recipient_role", "REGIONAL_OFFICER")), 1, due_at, application_id=app.id)
                if made:
                    created_count += 1
                    details.append(f"Created {threshold}% early-warning alert for {app.application_no}")

            # Optional reminders near the deadline are independently deduplicated.
            remaining = due_at - now
            if remaining.total_seconds() > 0:
                for window_hours in config.get("reminder_windows_hours", [48, 24]):
                    if window_hours > 0 and remaining <= timedelta(hours=int(window_hours)):
                        key = f"APP:{app.id}:STAGE:{app.current_stage_code}:{stage_token}:REMINDER:H{int(window_hours)}"
                        made = SLAEngine._create_notification_if_absent(
                            db, key, "STAGE_SLA_REMINDER", "WARNING",
                            f"Application {app.application_no} has {max(0, int(remaining.total_seconds() // 3600))} hour(s) left in {app.current_stage_code}; configured reminder window: {window_hours} hours.",
                            str(config.get("warning_recipient_role", "REGIONAL_OFFICER")), 1, due_at, application_id=app.id)
                        if made:
                            created_count += 1
                            details.append(f"Created {window_hours}-hour reminder for {app.application_no}")

        # EVC scheduling deadline: one warning window and a repeat-safe overdue notification.
        for evc in db.query(EVCEvent).filter(EVCEvent.status == "PENDING_SCHEDULE").all():
            evaluated += 1
            due = aware(evc.scheduling_deadline)
            app = evc.application
            if due <= now:
                key = f"EVC:{evc.id}:OVERDUE"
                made = SLAEngine._create_notification_if_absent(db, key, "EVC_OVERDUE", "CRITICAL",
                    f"EVC scheduling deadline has lapsed for application {app.application_no if app else evc.application_id}.",
                    "REGIONAL_OFFICER", 2, due, application_id=evc.application_id)
            elif due - now <= timedelta(hours=48):
                key = f"EVC:{evc.id}:WARN48"
                made = SLAEngine._create_notification_if_absent(db, key, "EVC_SCHEDULING_WARNING", "WARNING",
                    f"EVC scheduling deadline is within 48 hours for application {app.application_no if app else evc.application_id}.",
                    "REGIONAL_OFFICER", 1, due, application_id=evc.application_id)
            else:
                made = False
            if made:
                created_count += 1
                details.append(f"Created EVC deadline alert for {evc.application_id}")

        for und in db.query(Undertaking).filter(Undertaking.status.in_(["PENDING", "RETURNED_FOR_CORRECTION"])).all():
            evaluated += 1
            due, created_at = aware(und.due_at), aware(und.created_at or und.due_at)
            if due <= now:
                key = f"UND:{und.id}:OVERDUE"
                made = SLAEngine._create_notification_if_absent(db, key, "UNDERTAKING_DUE", "CRITICAL",
                    f"Compliance undertaking '{und.title}' is overdue.", "REGIONAL_OFFICER", 2, due,
                    application_id=und.application_id, undertaking_id=und.id)
            elif due - now <= timedelta(hours=72):
                key = f"UND:{und.id}:WARN72"
                made = SLAEngine._create_notification_if_absent(db, key, "UNDERTAKING_DUE", "WARNING",
                    f"Compliance undertaking '{und.title}' submission is due within 72 hours.", "INSTITUTION_USER", 1, due,
                    application_id=und.application_id, undertaking_id=und.id)
            else:
                made = False
            if made:
                created_count += 1
                details.append(f"Created deadline alert for undertaking {und.title}")

        for doc in db.query(Document).filter(Document.expiry_date.isnot(None), Document.status != "SUPERSEDED").all():
            evaluated += 1
            expiry = doc.expiry_date
            if expiry < today:
                if doc.status != "EXPIRED":
                    doc.status = "EXPIRED"
                key = f"DOC:{doc.id}:EXPIRED"
                made = SLAEngine._create_notification_if_absent(db, key, "DOCUMENT_EXPIRED", "CRITICAL",
                    f"Document '{doc.display_name}' ({doc.document_type}) expired on {expiry}.", "REGIONAL_OFFICER", 2,
                    datetime.combine(expiry, datetime.min.time(), tzinfo=timezone.utc), application_id=doc.application_id, document_id=doc.id)
            elif (expiry - today).days <= 30:
                if doc.status == "VALID":
                    doc.status = "EXPIRING_SOON"
                key = f"DOC:{doc.id}:EXPIRING"
                days_left = (expiry - today).days
                made = SLAEngine._create_notification_if_absent(db, key, "DOCUMENT_EXPIRING", "WARNING",
                    f"Document '{doc.display_name}' will expire in {days_left} day(s) ({expiry}); renewal required.", "INSTITUTION_USER", 1,
                    datetime.combine(expiry, datetime.min.time(), tzinfo=timezone.utc), application_id=doc.application_id, document_id=doc.id)
            else:
                made = False
            if made:
                created_count += 1
                details.append(f"Created document expiry alert for {doc.display_name}")

        db.commit()
        return evaluated, created_count, details

    @staticmethod
    def _create_notification_if_absent(
        db: Session, deduplication_key: str, notification_type: str, severity: str,
        message: str, recipient_role: str, escalation_level: int,
        due_at: Optional[datetime] = None, application_id: Optional[str] = None,
        undertaking_id: Optional[str] = None, document_id: Optional[str] = None
    ) -> bool:
        if db.query(Notification.id).filter(Notification.deduplication_key == deduplication_key).first():
            return False
        db.add(Notification(application_id=application_id, undertaking_id=undertaking_id,
            document_id=document_id, recipient_role=recipient_role, notification_type=notification_type,
            severity=severity, message=message, due_at=due_at, escalation_level=escalation_level,
            deduplication_key=deduplication_key, status="UNREAD"))
        db.flush()
        return True
