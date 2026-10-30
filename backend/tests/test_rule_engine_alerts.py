from datetime import datetime, timezone, timedelta
from app.models.entities import Application, Notification
from app.services.sla_engine import SLAEngine


def _prepare_single_target(db_session, target):
    now = datetime.now(timezone.utc)
    for app in db_session.query(Application).all():
        app.stage_entered_at = now
        app.stage_due_at = now + timedelta(days=20)
        app.current_stage_code = "SCRUTINY"
        app.workflow_status = "UNDER_REVIEW"
    target.stage_entered_at = now - timedelta(days=8)
    target.stage_due_at = now + timedelta(days=2)
    target.current_stage_code = "SCRUTINY"
    target.workflow_status = "UNDER_REVIEW"
    config = dict(target.workflow_template.configuration or {})
    config["warning_threshold_percent"] = 80
    config["escalation_ladder"] = [
        {"after_days": 0, "recipient_role": "REGIONAL_OFFICER"},
        {"after_days": 3, "recipient_role": "BUREAU_OFFICER"},
        {"after_days": 7, "recipient_role": "SYSTEM_ADMIN"},
    ]
    target.workflow_template.configuration = config
    db_session.query(Notification).delete()
    db_session.commit()
    return now


def test_80_percent_stage_warning_is_generated_once(db_session):
    target = db_session.query(Application).first()
    _prepare_single_target(db_session, target)
    _, created, _ = SLAEngine.evaluate_all(db_session)
    warnings = db_session.query(Notification).filter(
        Notification.application_id == target.id,
        Notification.notification_type == "STAGE_SLA_WARNING"
    ).all()
    assert created >= 1
    assert len(warnings) == 1
    assert "80%" in warnings[0].message
    _, second_created, _ = SLAEngine.evaluate_all(db_session)
    assert second_created == 0


def test_overdue_escalation_ladder_creates_each_eligible_level(db_session):
    target = db_session.query(Application).first()
    now = _prepare_single_target(db_session, target)
    target.stage_due_at = now - timedelta(days=8)
    target.stage_entered_at = now - timedelta(days=18)
    db_session.commit()
    SLAEngine.evaluate_all(db_session)
    alerts = db_session.query(Notification).filter(
        Notification.application_id == target.id,
        Notification.notification_type == "STAGE_SLA_BREACH"
    ).all()
    roles = {a.recipient_role for a in alerts}
    assert {"REGIONAL_OFFICER", "BUREAU_OFFICER", "SYSTEM_ADMIN"}.issubset(roles)
