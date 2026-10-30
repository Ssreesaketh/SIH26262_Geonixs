import uuid
from datetime import datetime, timezone, date
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Date, ForeignKey, Text, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Region(Base):
    __tablename__ = "regions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

    institutions = relationship("Institution", back_populates="region")
    users = relationship("User", back_populates="region")

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    institution_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    region_id = Column(String(36), ForeignKey("regions.id"), nullable=False, index=True)
    address = Column(Text, nullable=True)
    contact_email = Column(String(150), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    region = relationship("Region", back_populates="institutions")
    users = relationship("User", back_populates="institution")
    applications = relationship("Application", back_populates="institution")
    undertakings = relationship("Undertaking", back_populates="institution")
    documents = relationship("Document", back_populates="institution")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(150), nullable=False)
    role = Column(String(50), nullable=False, index=True) # INSTITUTION_USER, REGIONAL_OFFICER, BUREAU_OFFICER, EVC_MEMBER, SYSTEM_ADMIN
    region_id = Column(String(36), ForeignKey("regions.id"), nullable=True, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    region = relationship("Region", back_populates="users")
    institution = relationship("Institution", back_populates="users")

class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    code = Column(String(50), nullable=False, index=True) # ONLY_SCRUTINY, SCRUTINY_EVC, EVC_SAC_SHC
    name = Column(String(150), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    configuration = Column(JSON, nullable=False) # Stages, transitions, SLA days, roles
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("code", "version", name="uq_workflow_code_version"),
    )

class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_no = Column(String(50), unique=True, nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    application_type = Column(String(50), nullable=False) # NEW_INSTITUTION, EXTENSION_OF_APPROVAL, INTAKE_VARIATION
    workflow_template_id = Column(String(36), ForeignKey("workflow_templates.id"), nullable=False)
    workflow_version = Column(Integer, nullable=False, default=1)
    current_stage_code = Column(String(50), nullable=False, index=True) # DRAFT, SCRUTINY, EVC, SAC_SHC, COMPLETED
    workflow_status = Column(String(50), nullable=False, index=True) # DRAFT, SUBMITTED, UNDER_REVIEW, DEFICIENCY_RETURNED, STAGE_COMPLETED
    decision_status = Column(String(50), nullable=False, default="NOT_RECORDED") # NOT_RECORDED, RECOMMENDED_APPROVAL, RECOMMENDED_REJECTION
    assigned_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    assigned_role = Column(String(50), nullable=False, default="REGIONAL_OFFICER")
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    stage_entered_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    stage_due_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    institution = relationship("Institution", back_populates="applications")
    assigned_user = relationship("User", foreign_keys=[assigned_user_id])
    workflow_template = relationship("WorkflowTemplate")
    events = relationship("ApplicationEvent", back_populates="application", order_by="ApplicationEvent.created_at.asc()")
    evc_events = relationship("EVCEvent", back_populates="application")
    undertakings = relationship("Undertaking", back_populates="application")
    documents = relationship("Document", back_populates="application")
    notifications = relationship("Notification", back_populates="application")

class ApplicationEvent(Base):
    __tablename__ = "application_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    actor_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    actor_role = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False) # CREATE, SUBMIT, ADVANCE, RETURN_DEFICIENCY, RESUBMIT, VERIFY, SCHEDULE_EVC
    from_stage = Column(String(50), nullable=True)
    to_stage = Column(String(50), nullable=True)
    reason = Column(Text, nullable=True)
    metadata_json = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)

    application = relationship("Application", back_populates="events")
    actor = relationship("User", foreign_keys=[actor_user_id])

class EVCEvent(Base):
    __tablename__ = "evc_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="PENDING_SCHEDULE") # PENDING_SCHEDULE, SCHEDULED, VISIT_COMPLETED, FINDINGS_SUBMITTED
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    scheduling_deadline = Column(DateTime(timezone=True), nullable=False)
    committee_details = Column(JSON, default={})
    findings_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    application = relationship("Application", back_populates="evc_events")

class Undertaking(Base):
    __tablename__ = "undertakings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="PENDING") # PENDING, SUBMITTED, VERIFIED, RETURNED_FOR_CORRECTION
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    evidence_summary = Column(Text, nullable=True)
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    application = relationship("Application", back_populates="undertakings")
    institution = relationship("Institution", back_populates="undertakings")
    verifier = relationship("User", foreign_keys=[verified_by])
    documents = relationship("Document", back_populates="undertaking")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=True, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    undertaking_id = Column(String(36), ForeignKey("undertakings.id"), nullable=True, index=True)
    document_type = Column(String(100), nullable=False, index=True) # LAND_LEASE_DEED, FIRE_NOC, BUILDING_STABILITY_CERT, AICTE_AFFIDAVIT, UNDERTAKING_EVIDENCE
    display_name = Column(String(255), nullable=False)
    storage_key = Column(String(255), unique=True, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    expiry_date = Column(Date, nullable=True, index=True)
    status = Column(String(50), nullable=False, default="VALID") # VALID, EXPIRING_SOON, EXPIRED, SUPERSEDED
    renewal_of_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now)
    verified_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_remarks = Column(Text, nullable=True)

    application = relationship("Application", back_populates="documents")
    institution = relationship("Institution", back_populates="documents")
    undertaking = relationship("Undertaking", back_populates="documents")
    verifier = relationship("User", foreign_keys=[verified_by])
    renewed_from = relationship("Document", remote_side=[id])

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=True, index=True)
    undertaking_id = Column(String(36), ForeignKey("undertakings.id"), nullable=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    recipient_role = Column(String(50), nullable=False, index=True)
    recipient_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    notification_type = Column(String(50), nullable=False, index=True) # STAGE_SLA_WARNING, STAGE_SLA_BREACH, EVC_OVERDUE, UNDERTAKING_DUE, DOCUMENT_EXPIRING, DOCUMENT_EXPIRED
    severity = Column(String(20), nullable=False, default="INFO") # INFO, WARNING, CRITICAL
    message = Column(Text, nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    escalation_level = Column(Integer, default=1, nullable=False)
    deduplication_key = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(50), default="UNREAD", nullable=False) # UNREAD, ACKNOWLEDGED, RESOLVED
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    application = relationship("Application", back_populates="notifications")


class AuditChainEntry(Base):
    """Append-only hash-chain snapshot for consequential application events.

    The payload is retained independently of ApplicationEvent so verification still
    works if an application event is accidentally edited or removed.
    """
    __tablename__ = "audit_chain_entries"

    sequence = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    previous_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False, unique=True)
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class DocumentEvaluation(Base):
    """Persisted AI-assisted document review; it is advisory, never an approval decision."""
    __tablename__ = "document_evaluations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, index=True)
    institution_id = Column(String(36), ForeignKey("institutions.id"), nullable=False, index=True)
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=True, index=True)
    evaluator_user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="COMPLETED")
    content_sha256 = Column(String(64), nullable=False)
    engine_mode = Column(String(50), nullable=False)
    report_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    document = relationship("Document")
    institution = relationship("Institution")
    application = relationship("Application")
    evaluator = relationship("User")


class RegulatoryChunk(Base):
    """Text chunks from administrator-approved regulatory source documents."""
    __tablename__ = "regulatory_chunks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    source_title = Column(String(255), nullable=False, index=True)
    source_url = Column(String(1000), nullable=True)
    source_version = Column(String(100), nullable=True)
    page_number = Column(Integer, nullable=True)
    chunk_text = Column(Text, nullable=False)
    # Optional local embedding vector. Kept in JSON for a dependency-light prototype;
    # production-scale similarity search should move this field to pgvector.
    embedding_json = Column(JSON, nullable=True)
    content_sha256 = Column(String(64), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    uploaded_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)

    uploaded_by = relationship("User")
