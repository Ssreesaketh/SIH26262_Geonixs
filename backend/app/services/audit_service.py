import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.entities import ApplicationEvent, AuditChainEntry, User

GENESIS_HASH = "0" * 64

def _canonical_json(value: Dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)

def _hash_entry(previous_hash: str, payload: Dict[str, Any]) -> str:
    return hashlib.sha256((previous_hash + _canonical_json(payload)).encode("utf-8")).hexdigest()

class AuditService:
    @staticmethod
    def record_event(
        db: Session, application_id: str, actor: User, action: str,
        from_stage: Optional[str] = None, to_stage: Optional[str] = None,
        reason: Optional[str] = None, metadata_json: Optional[Dict[str, Any]] = None
    ) -> ApplicationEvent:
        """Write the event and its tamper-evident chain entry in the same transaction."""
        event = ApplicationEvent(
            application_id=application_id, actor_user_id=actor.id, actor_role=actor.role,
            action=action, from_stage=from_stage, to_stage=to_stage, reason=reason,
            metadata_json=metadata_json or {}
        )
        db.add(event)
        db.flush()
        created_at = event.created_at or datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        payload = {
            "event_id": event.id, "application_id": event.application_id,
            "actor_user_id": event.actor_user_id, "actor_role": event.actor_role,
            "action": event.action, "from_stage": event.from_stage, "to_stage": event.to_stage,
            "reason": event.reason, "metadata_json": event.metadata_json or {},
            "created_at": created_at.isoformat()
        }
        # Serialize chain-head updates. SQLite serializes writes; PostgreSQL gets an
        # explicit table lock so even the first two concurrent entries cannot fork.
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.execute(text("LOCK TABLE audit_chain_entries IN EXCLUSIVE MODE"))
        last = db.query(AuditChainEntry).order_by(AuditChainEntry.sequence.desc()).with_for_update().first()
        previous_hash = last.entry_hash if last else GENESIS_HASH
        chain_entry = AuditChainEntry(
            event_id=event.id, previous_hash=previous_hash,
            entry_hash=_hash_entry(previous_hash, payload), payload=payload
        )
        db.add(chain_entry)
        db.flush()
        return event

    @staticmethod
    def record_system_event(db: Session, actor: User, action: str, target_type: str, target_id: str, details: Dict[str, Any]) -> AuditChainEntry:
        """Chain an administrative/system event that has no application event row."""
        import uuid
        created_at = datetime.now(timezone.utc)
        payload = {
            "event_id": "SYS-" + str(uuid.uuid4()), "application_id": None,
            "actor_user_id": actor.id, "actor_role": actor.role, "action": action,
            "from_stage": None, "to_stage": None, "reason": None,
            "metadata_json": {"target_type": target_type, "target_id": target_id, "details": details},
            "created_at": created_at.isoformat()
        }
        if db.bind is not None and db.bind.dialect.name == "postgresql":
            db.execute(text("LOCK TABLE audit_chain_entries IN EXCLUSIVE MODE"))
        last = db.query(AuditChainEntry).order_by(AuditChainEntry.sequence.desc()).with_for_update().first()
        previous_hash = last.entry_hash if last else GENESIS_HASH
        entry = AuditChainEntry(event_id=payload["event_id"], previous_hash=previous_hash,
                                entry_hash=_hash_entry(previous_hash, payload), payload=payload)
        db.add(entry)
        db.flush()
        return entry

    @staticmethod
    def verify_chain(db: Session) -> Dict[str, Any]:
        entries = db.query(AuditChainEntry).order_by(AuditChainEntry.sequence.asc()).all()
        expected_previous = GENESIS_HASH
        for entry in entries:
            if entry.previous_hash != expected_previous:
                return {"valid": False, "entries_checked": entry.sequence, "failed_sequence": entry.sequence, "reason": "previous_hash_mismatch"}
            expected_hash = _hash_entry(entry.previous_hash, entry.payload)
            if expected_hash != entry.entry_hash:
                return {"valid": False, "entries_checked": entry.sequence, "failed_sequence": entry.sequence, "reason": "entry_hash_mismatch"}
            # Compare the immutable snapshot with the operational event too. System
            # events use SYS- IDs and intentionally have no ApplicationEvent row.
            if not str(entry.event_id).startswith("SYS-"):
                event = db.query(ApplicationEvent).filter(ApplicationEvent.id == entry.event_id).first()
                if event is None:
                    return {"valid": False, "entries_checked": entry.sequence, "failed_sequence": entry.sequence, "reason": "source_event_missing"}
                event_time_value = event.created_at
                if event_time_value and event_time_value.tzinfo is None:
                    event_time_value = event_time_value.replace(tzinfo=timezone.utc)
                event_time = event_time_value.isoformat() if event_time_value else None
                live_payload = {
                    "event_id": event.id, "application_id": event.application_id,
                    "actor_user_id": event.actor_user_id, "actor_role": event.actor_role,
                    "action": event.action, "from_stage": event.from_stage, "to_stage": event.to_stage,
                    "reason": event.reason, "metadata_json": event.metadata_json or {},
                    "created_at": event_time
                }
                if _canonical_json(live_payload) != _canonical_json(entry.payload):
                    return {"valid": False, "entries_checked": entry.sequence, "failed_sequence": entry.sequence, "reason": "source_event_mismatch"}
            expected_previous = entry.entry_hash
        return {"valid": True, "entries_checked": len(entries), "failed_sequence": None, "reason": None, "head_hash": expected_previous}
