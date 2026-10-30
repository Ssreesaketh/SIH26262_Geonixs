export type Role =
  | 'INSTITUTION_USER'
  | 'REGIONAL_OFFICER'
  | 'BUREAU_OFFICER'
  | 'SYSTEM_ADMIN';

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: Role;
  region_id?: string | null;
  institution_id?: string | null;
  is_active: boolean;
  created_at: string;
}

export interface Region {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
}

export interface Institution {
  id: string;
  institution_code: string;
  name: string;
  region_id: string;
  address?: string | null;
  contact_email: string;
  created_at: string;
  region?: Region | null;
}

export interface WorkflowTemplate {
  id: string;
  code: string;
  name: string;
  version: number;
  configuration: {
    ordered_stages: string[];
    stage_slas: Record<string, number>;
    rectification_sla_days?: number;
  };
  is_active: boolean;
  created_at: string;
}

export interface Application {
  id: string;
  application_no: string;
  institution_id: string;
  application_type: string;
  workflow_template_id: string;
  workflow_version: number;
  current_stage_code: string;
  workflow_status: string;
  decision_status: string;
  assigned_user_id?: string | null;
  assigned_role: string;
  submitted_at?: string | null;
  stage_entered_at: string;
  stage_due_at: string;
  created_at: string;
  updated_at: string;
  institution_name?: string | null;
  region_code?: string | null;
}

export interface ApplicationEvent {
  id: string;
  application_id: string;
  actor_user_id: string;
  actor_role: string;
  action: string;
  from_stage?: string | null;
  to_stage?: string | null;
  reason?: string | null;
  metadata_json?: Record<string, any>;
  created_at: string;
  actor_name?: string | null;
}

export interface EVCEvent {
  id: string;
  application_id: string;
  status: string;
  scheduled_date?: string | null;
  scheduling_deadline: string;
  committee_details: Record<string, any>;
  findings_summary?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface Undertaking {
  id: string;
  application_id: string;
  institution_id: string;
  title: string;
  description: string;
  due_at: string;
  status: string;
  submitted_at?: string | null;
  evidence_summary?: string | null;
  verified_by?: string | null;
  verified_at?: string | null;
  verification_remarks?: string | null;
  created_at: string;
}

export interface DocumentItem {
  id: string;
  application_id?: string | null;
  institution_id: string;
  undertaking_id?: string | null;
  document_type: string;
  display_name: string;
  storage_key: string;
  mime_type: string;
  file_size: number;
  expiry_date?: string | null;
  status: 'SUBMITTED' | 'VERIFIED' | 'RETURNED_FOR_CORRECTION' | 'VALID' | 'EXPIRING_SOON' | 'EXPIRED' | 'SUPERSEDED';
  renewal_of_id?: string | null;
  submitted_at: string;
  verified_by?: string | null;
  verified_at?: string | null;
  verification_remarks?: string | null;
}

export interface NotificationItem {
  id: string;
  application_id?: string | null;
  undertaking_id?: string | null;
  document_id?: string | null;
  recipient_role: string;
  recipient_user_id?: string | null;
  notification_type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  message: string;
  due_at?: string | null;
  escalation_level: number;
  deduplication_key: string;
  status: 'UNREAD' | 'ACKNOWLEDGED' | 'RESOLVED';
  acknowledged_at?: string | null;
  created_at: string;
  application_no?: string | null;
}

export interface DashboardSummary {
  total_active: number;
  overdue_stages: number;
  upcoming_sla: number;
  expired_documents: number;
  pending_evc: number;
  pending_undertakings: number;
}

export interface StagePendency {
  stage_code: string;
  stage_name: string;
  count: number;
}

export interface RegionalWorkload {
  region_id: string;
  region_code: string;
  region_name: string;
  active_count: number;
  overdue_count: number;
}
