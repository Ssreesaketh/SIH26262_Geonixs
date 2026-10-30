from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date

# Auth Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserBase(BaseModel):
    email: EmailStr
    display_name: str
    role: str
    region_id: Optional[str] = None
    institution_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Region & Institution Schemas
class RegionResponse(BaseModel):
    id: str
    code: str
    name: str
    is_active: bool

    class Config:
        from_attributes = True

class InstitutionResponse(BaseModel):
    id: str
    institution_code: str
    name: str
    region_id: str
    address: Optional[str] = None
    contact_email: str
    created_at: datetime
    region: Optional[RegionResponse] = None

    class Config:
        from_attributes = True

# Workflow Schemas
class WorkflowTemplateResponse(BaseModel):
    id: str
    code: str
    name: str
    version: int
    configuration: Dict[str, Any]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowTemplateUpdate(BaseModel):
    configuration: Dict[str, Any]

# Application Events (Audit)
class ApplicationEventResponse(BaseModel):
    id: str
    application_id: str
    actor_user_id: str
    actor_role: str
    action: str
    from_stage: Optional[str] = None
    to_stage: Optional[str] = None
    reason: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    actor_name: Optional[str] = None

    class Config:
        from_attributes = True

# EVC Schemas
class EVCScheduleRequest(BaseModel):
    scheduled_date: datetime
    committee_details: Dict[str, Any] = Field(default_factory=dict)

class EVCCompleteRequest(BaseModel):
    findings_summary: str
    outcome: str = "RECOMMENDED" # RECOMMENDED, DEFICIENT

class EVCEventResponse(BaseModel):
    id: str
    application_id: str
    status: str
    scheduled_date: Optional[datetime] = None
    scheduling_deadline: datetime
    committee_details: Dict[str, Any]
    findings_summary: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Undertakings
class UndertakingCreate(BaseModel):
    title: str
    description: str
    due_at: datetime

class UndertakingSubmitRequest(BaseModel):
    evidence_summary: str

class UndertakingVerifyRequest(BaseModel):
    approved: bool
    verification_remarks: str

class UndertakingResponse(BaseModel):
    id: str
    application_id: str
    institution_id: str
    title: str
    description: str
    due_at: datetime
    status: str
    submitted_at: Optional[datetime] = None
    evidence_summary: Optional[str] = None
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Documents
class DocumentResponse(BaseModel):
    id: str
    application_id: Optional[str] = None
    institution_id: str
    undertaking_id: Optional[str] = None
    document_type: str
    display_name: str
    mime_type: str
    file_size: int
    expiry_date: Optional[date] = None
    status: str
    renewal_of_id: Optional[str] = None
    submitted_at: datetime
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    verification_remarks: Optional[str] = None

    class Config:
        from_attributes = True

# Application Schemas
class ApplicationCreate(BaseModel):
    institution_id: str
    application_type: str = "EXTENSION_OF_APPROVAL" # NEW_INSTITUTION, EXTENSION_OF_APPROVAL, INTAKE_VARIATION
    workflow_template_code: str = "SCRUTINY_EVC" # Default template

class ApplicationActionRequest(BaseModel):
    action: str # ADVANCE, RETURN_DEFICIENCY, RESUBMIT, RECOMMEND_DECISION
    reason: Optional[str] = None
    target_stage: Optional[str] = None
    decision_status: Optional[str] = None # When action is RECOMMEND_DECISION

class ApplicationResponse(BaseModel):
    id: str
    application_no: str
    institution_id: str
    application_type: str
    workflow_template_id: str
    workflow_version: int
    current_stage_code: str
    workflow_status: str
    decision_status: str
    assigned_user_id: Optional[str] = None
    assigned_role: str
    submitted_at: Optional[datetime] = None
    stage_entered_at: datetime
    stage_due_at: datetime
    created_at: datetime
    updated_at: datetime
    institution_name: Optional[str] = None
    region_code: Optional[str] = None

    class Config:
        from_attributes = True

class ApplicationDetailResponse(ApplicationResponse):
    institution: Optional[InstitutionResponse] = None
    events: List[ApplicationEventResponse] = []
    evc_events: List[EVCEventResponse] = []
    undertakings: List[UndertakingResponse] = []
    documents: List[DocumentResponse] = []
    permitted_actions: List[str] = []

class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int

# Notifications & Alerts
class NotificationResponse(BaseModel):
    id: str
    application_id: Optional[str] = None
    undertaking_id: Optional[str] = None
    document_id: Optional[str] = None
    recipient_role: str
    recipient_user_id: Optional[str] = None
    notification_type: str
    severity: str
    message: str
    due_at: Optional[datetime] = None
    escalation_level: int
    deduplication_key: str
    status: str
    acknowledged_at: Optional[datetime] = None
    created_at: datetime
    application_no: Optional[str] = None

    class Config:
        from_attributes = True

class AlertCheckResponse(BaseModel):
    total_evaluated: int
    new_alerts_created: int
    checked_at: datetime
    details: List[str] = []

class NotificationAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None

# Dashboard Schemas
class DashboardSummaryResponse(BaseModel):
    total_active: int
    overdue_stages: int
    upcoming_sla: int
    expired_documents: int
    pending_evc: int
    pending_undertakings: int

class StagePendencyItem(BaseModel):
    stage_code: str
    stage_name: str
    count: int

class RegionalWorkloadItem(BaseModel):
    region_id: str
    region_code: str
    region_name: str
    active_count: int
    overdue_count: int

TokenResponse.model_rebuild()
