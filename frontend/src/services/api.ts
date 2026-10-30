import {
  User,
  DashboardSummary,
  StagePendency,
  RegionalWorkload,
  Application,
  ApplicationEvent,
  EVCEvent,
  Undertaking,
  DocumentItem,
  NotificationItem,
  WorkflowTemplate
} from '../types';

const BASE_URL = '/api/v1';

export function getToken(): string | null {
  return localStorage.getItem('aicte_token');
}

export function setToken(token: string) {
  localStorage.setItem('aicte_token', token);
}

export function clearToken() {
  localStorage.removeItem('aicte_token');
  localStorage.removeItem('aicte_user');
}

export function getStoredUser(): User | null {
  const u = localStorage.getItem('aicte_user');
  return u ? JSON.parse(u) : null;
}

export function setStoredUser(user: User) {
  localStorage.setItem('aicte_user', JSON.stringify(user));
}

async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers || {});

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (res.status === 401) {
    clearToken();
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
    throw new Error('Session expired or unauthorized');
  }

  if (!res.ok) {
    let errMsg = `Request failed (${res.status})`;
    try {
      const errData = await res.json();
      errMsg = errData.detail || errData.message || errMsg;
    } catch (_) {}
    throw new Error(errMsg);
  }

  return res.json();
}

async function downloadAuthenticatedFile(endpoint: string, defaultFilename: string): Promise<void> {
  const token = getToken();
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  if (response.status === 401) {
    clearToken();
    window.location.href = '/login';
    throw new Error('Session expired or unauthorized');
  }
  if (!response.ok) {
    let message = `Download failed (${response.status})`;
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch (_) {}
    throw new Error(message);
  }
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const disposition = response.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1] || defaultFilename;
  const anchor = document.createElement('a');
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}

export const api = {
  // Auth
  async login(email: string, password: string) {
    const data = await apiFetch<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
    setToken(data.access_token);
    setStoredUser(data.user);
    return data;
  },

  async logout() {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } catch (_) {}
    clearToken();
  },

  async getMe(): Promise<User> {
    const user = await apiFetch<User>('/auth/me');
    setStoredUser(user);
    return user;
  },

  // Dashboard
  async getDashboardSummary(): Promise<DashboardSummary> {
    return apiFetch<DashboardSummary>('/dashboard/summary');
  },

  async getStagePendency(): Promise<StagePendency[]> {
    return apiFetch<StagePendency[]>('/dashboard/pendency');
  },

  async getRegionalWorkload(): Promise<RegionalWorkload[]> {
    return apiFetch<RegionalWorkload[]>('/dashboard/regions');
  },

  // Applications
  async listApplications(params: {
    page?: number;
    pageSize?: number;
    stage?: string;
    status?: string;
    regionId?: string;
    search?: string;
  }): Promise<{ items: Application[]; total: number; page: number; page_size: number }> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.pageSize) query.set('page_size', params.pageSize.toString());
    if (params.stage) query.set('stage', params.stage);
    if (params.status) query.set('status', params.status);
    if (params.regionId) query.set('region_id', params.regionId);
    if (params.search) query.set('search', params.search);

    return apiFetch(`/applications?${query.toString()}`);
  },

  async getApplication(id: string): Promise<Application & {
    events: ApplicationEvent[];
    evc_events: EVCEvent[];
    undertakings: Undertaking[];
    documents: DocumentItem[];
    permitted_actions: string[];
    institution?: any;
  }> {
    return apiFetch(`/applications/${id}`);
  },

  async createApplication(payload: {
    institution_id: string;
    application_type: string;
    workflow_template_code: string;
  }): Promise<Application> {
    return apiFetch('/applications', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async submitApplication(id: string): Promise<any> {
    return apiFetch(`/applications/${id}/submit`, { method: 'POST' });
  },

  async executeApplicationAction(id: string, payload: {
    action: string;
    reason?: string;
    target_stage?: string;
    decision_status?: string;
  }): Promise<any> {
    return apiFetch(`/applications/${id}/actions`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async getApplicationHistory(id: string): Promise<ApplicationEvent[]> {
    return apiFetch(`/applications/${id}/history`);
  },

  // EVC
  async listEvc(statusFilter?: string): Promise<EVCEvent[]> {
    const q = statusFilter ? `?status_filter=${statusFilter}` : '';
    return apiFetch(`/evc${q}`);
  },

  async scheduleEvc(applicationId: string, payload: {
    scheduled_date: string;
    committee_details: Record<string, any>;
  }): Promise<EVCEvent> {
    return apiFetch(`/evc/applications/${applicationId}`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async completeEvc(id: string, payload: {
    findings_summary: string;
    outcome: string;
  }): Promise<EVCEvent> {
    return apiFetch(`/evc/${id}/complete`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  // Compliance (Undertakings)
  async listCompliance(statusFilter?: string): Promise<Undertaking[]> {
    const q = statusFilter ? `?status_filter=${statusFilter}` : '';
    return apiFetch(`/compliance${q}`);
  },

  async createUndertaking(applicationId: string, payload: {
    title: string;
    description: string;
    due_at: string;
  }): Promise<Undertaking> {
    return apiFetch(`/compliance/applications/${applicationId}`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },

  async submitUndertakingEvidence(id: string, evidenceSummary: string): Promise<Undertaking> {
    return apiFetch(`/compliance/${id}/submit`, {
      method: 'POST',
      body: JSON.stringify({ evidence_summary: evidenceSummary })
    });
  },

  async verifyUndertaking(id: string, approved: boolean, remarks: string): Promise<Undertaking> {
    return apiFetch(`/compliance/${id}/verify`, {
      method: 'POST',
      body: JSON.stringify({ approved, verification_remarks: remarks })
    });
  },

  // Documents and role-scoped downloadable forms
  async listForms(): Promise<Array<{ key: string; title: string; description: string; filename: string; audience: string; download_url: string }>> {
    return apiFetch('/documents/forms');
  },

  async downloadForm(key: string): Promise<void> {
    return downloadAuthenticatedFile(`/documents/forms/${encodeURIComponent(key)}/download`, `${key}.pdf`);
  },

  async downloadDocument(id: string): Promise<void> {
    return downloadAuthenticatedFile(`/documents/${encodeURIComponent(id)}/download`, `document-${id}.pdf`);
  },

  async listDocuments(statusFilter?: string, docType?: string): Promise<DocumentItem[]> {
    const q = new URLSearchParams();
    if (statusFilter) q.set('status_filter', statusFilter);
    if (docType) q.set('document_type', docType);
    return apiFetch(`/documents?${q.toString()}`);
  },

  async uploadDocument(formData: FormData): Promise<DocumentItem> {
    return apiFetch('/documents/upload', {
      method: 'POST',
      body: formData
    });
  },

  async renewDocument(id: string, formData: FormData): Promise<DocumentItem> {
    return apiFetch(`/documents/${id}/renew`, {
      method: 'POST',
      body: formData
    });
  },

  // AI-assisted PDF evaluation and regulatory RAG. AI findings are advisory only.
  async evaluateDocument(id: string): Promise<any> {
    return apiFetch(`/ai/documents/${encodeURIComponent(id)}/evaluate`, { method: 'POST' });
  },

  async listDocumentEvaluations(id: string): Promise<any[]> {
    return apiFetch(`/ai/documents/${encodeURIComponent(id)}/evaluations`);
  },

  async askRegulatoryQuestion(question: string): Promise<any> {
    return apiFetch('/ai/ask', { method: 'POST', body: JSON.stringify({ question }) });
  },

  async listRegulatorySources(): Promise<any[]> {
    return apiFetch('/ai/knowledge');
  },

  async uploadRegulatorySource(formData: FormData): Promise<any> {
    return apiFetch('/ai/knowledge/upload', { method: 'POST', body: formData });
  },

  async deactivateRegulatorySource(hash: string): Promise<any> {
    return apiFetch(`/ai/knowledge/${encodeURIComponent(hash)}/deactivate`, { method: 'POST' });
  },

  async reviewDocument(id: string, status: 'VERIFIED' | 'RETURNED_FOR_CORRECTION', remarks: string): Promise<DocumentItem> {
    return apiFetch(`/documents/${encodeURIComponent(id)}/review`, {
      method: 'POST',
      body: JSON.stringify({ status, remarks })
    });
  },

  getDocumentDownloadUrl(id: string): string {
    return `${BASE_URL}/documents/${id}/download`;
  },

  // Alerts
  async listAlerts(severity?: string, statusFilter?: string): Promise<NotificationItem[]> {
    const q = new URLSearchParams();
    if (severity) q.set('severity', severity);
    if (statusFilter) q.set('status_filter', statusFilter);
    return apiFetch(`/alerts?${q.toString()}`);
  },

  async checkDeadlines(): Promise<{
    total_evaluated: number;
    new_alerts_created: number;
    checked_at: string;
    details: string[];
  }> {
    return apiFetch('/alerts/check', { method: 'POST' });
  },

  async acknowledgeAlert(id: string): Promise<NotificationItem> {
    return apiFetch(`/alerts/${id}/acknowledge`, { method: 'POST' });
  },

  async resolveAlert(id: string): Promise<NotificationItem> {
    return apiFetch(`/alerts/${id}/resolve`, { method: 'POST' });
  },

  // Workflows & Admin
  async listWorkflows(): Promise<WorkflowTemplate[]> {
    return apiFetch('/config/workflows');
  },

  async updateWorkflow(id: string, configuration: any): Promise<WorkflowTemplate> {
    return apiFetch(`/config/workflows/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ configuration })
    });
  },

  async verifyAuditChain(): Promise<{ valid: boolean; entries_checked: number; failed_sequence?: number | null; reason?: string | null; head_hash?: string }> {
    return apiFetch('/config/audit/verify');
  },

  async resetDemo(): Promise<{ message: string }> {
    return apiFetch('/admin/reset-demo', { method: 'POST' });
  }
};
