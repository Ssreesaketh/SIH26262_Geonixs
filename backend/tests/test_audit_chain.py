from app.models.entities import Application, User, AuditChainEntry
from app.services.audit_service import AuditService


def test_audit_chain_detects_payload_tampering(db_session):
    app = db_session.query(Application).first()
    actor = db_session.query(User).filter(User.email == "admin@aicte.gov.in").first()
    AuditService.record_event(db_session, app.id, actor, "TEST_AUDIT_CHAIN", from_stage=app.current_stage_code, to_stage=app.current_stage_code)
    db_session.commit()
    result = AuditService.verify_chain(db_session)
    assert result["valid"] is True, result
    entry = db_session.query(AuditChainEntry).order_by(AuditChainEntry.sequence.desc()).first()
    original = dict(entry.payload)
    entry.payload = {**original, "action": "TAMPERED"}
    db_session.flush()
    result = AuditService.verify_chain(db_session)
    assert result["valid"] is False
    assert result["reason"] == "entry_hash_mismatch"
    entry.payload = original
    db_session.commit()
    assert AuditService.verify_chain(db_session)["valid"] is True


def test_system_audit_events_are_chained(db_session):
    actor = db_session.query(User).filter(User.email == "admin@aicte.gov.in").first()
    AuditService.record_system_event(db_session, actor, "TEST_ADMIN_EVENT", "Test", "id-1", {"value": 1})
    db_session.commit()
    assert AuditService.verify_chain(db_session)["valid"] is True


def test_audit_chain_detects_source_event_changes(db_session):
    app = db_session.query(Application).first()
    actor = db_session.query(User).filter(User.email == "admin@aicte.gov.in").first()
    event = AuditService.record_event(db_session, app.id, actor, "TEST_SOURCE_TAMPER")
    db_session.commit()
    event.action = "ALTERED_AFTER_INSERT"
    db_session.commit()
    result = AuditService.verify_chain(db_session)
    assert result["valid"] is False
    assert result["reason"] == "source_event_mismatch"
