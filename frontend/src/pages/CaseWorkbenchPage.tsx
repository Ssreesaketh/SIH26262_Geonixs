import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Application, ApplicationEvent, EVCEvent, Undertaking, DocumentItem, User } from '../types';
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Send,
  Upload,
  FileText,
  Clock,
  History,
  ShieldCheck,
  CalendarCheck,
  Building2,
  FolderOpen,
  Download
} from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { WorkflowStepper } from '../components/WorkflowStepper';
import { Modal } from '../components/Modal';

interface CaseWorkbenchPageProps {
  applicationId: string;
  user: User;
  onBack: () => void;
}

export const CaseWorkbenchPage: React.FC<CaseWorkbenchPageProps> = ({
  applicationId,
  user,
  onBack
}) => {
  const [app, setApp] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'docs' | 'compliance' | 'evc' | 'audit'>('docs');
  const [actionLoading, setActionLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Modals
  const [showDeficiencyModal, setShowDeficiencyModal] = useState(false);
  const [deficiencyReason, setDeficiencyReason] = useState('');

  const [showResubmitModal, setShowResubmitModal] = useState(false);
  const [resubmitReason, setResubmitReason] = useState('');

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDocType, setUploadDocType] = useState('LAND_LEASE_DEED');
  const [uploadExpiry, setUploadExpiry] = useState('');

  const [showVerifyUndModal, setShowVerifyUndModal] = useState(false);
  const [selectedUndId, setSelectedUndId] = useState<string | null>(null);
  const [verifyApproved, setVerifyApproved] = useState(true);
  const [verifyRemarks, setVerifyRemarks] = useState('');

  const loadApplication = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const data = await api.getApplication(applicationId);
      setApp(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load case data');
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadApplication();
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void loadApplication(false);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [applicationId]);

  const handleAdvance = async () => {
    if (!confirm('Advance this application to the next configured workflow stage?')) return;
    setActionLoading(true);
    try {
      await api.executeApplicationAction(applicationId, {
        action: 'ADVANCE',
        reason: 'Officer verified procedural stage requirements and advanced application.'
      });
      await loadApplication();
    } catch (err: any) {
      alert(err.message || 'Action failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitInitial = async () => {
    setActionLoading(true);
    try {
      await api.submitApplication(applicationId);
      await loadApplication();
    } catch (err: any) {
      alert(err.message || 'Submission failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReturnDeficiency = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!deficiencyReason.trim()) {
      alert('A detailed justification is mandatory when issuing a deficiency notice.');
      return;
    }
    setActionLoading(true);
    try {
      await api.executeApplicationAction(applicationId, {
        action: 'RETURN_DEFICIENCY',
        reason: deficiencyReason.trim()
      });
      setShowDeficiencyModal(false);
      setDeficiencyReason('');
      await loadApplication();
    } catch (err: any) {
      alert(err.message || 'Return failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleResubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    try {
      await api.executeApplicationAction(applicationId, {
        action: 'RESUBMIT',
        reason: resubmitReason.trim() || 'Institution submitted revised compliance responses.'
      });
      setShowResubmitModal(false);
      setResubmitReason('');
      await loadApplication();
    } catch (err: any) {
      alert(err.message || 'Resubmission failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUploadDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    setActionLoading(true);
    try {
      const fd = new FormData();
      fd.append('file', uploadFile);
      fd.append('document_type', uploadDocType);
      fd.append('application_id', applicationId);

const institutionId = app?.institution_id || user?.institution_id;

if (!institutionId) {
  alert('Institution ID is missing. Please log in again and retry.');
  setActionLoading(false);
  return;
}

fd.append('institution_id', institutionId);

if (uploadExpiry) fd.append('expiry_date_str', uploadExpiry);

      await api.uploadDocument(fd);
      setShowUploadModal(false);
      setUploadFile(null);
      await loadApplication();
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerifyUndertaking = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUndId) return;
    setActionLoading(true);
    try {
      await api.verifyUndertaking(selectedUndId, verifyApproved, verifyRemarks);
      setShowVerifyUndModal(false);
      setSelectedUndId(null);
      setVerifyRemarks('');
      await loadApplication();
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRecommendDecision = async (decision: 'RECOMMENDED_APPROVAL' | 'RECOMMENDED_REJECTION') => {
    const rationale = window.prompt('Enter the Bureau Officer recommendation rationale (required):');
    if (!rationale || !rationale.trim()) return;
    setActionLoading(true);
    try {
      await api.executeApplicationAction(applicationId, {
        action: 'RECOMMEND_DECISION',
        decision_status: decision,
        reason: rationale.trim()
      });
      await loadApplication();
    } catch (err: any) {
      alert(err.message || 'Recommendation failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleFinalDecision = async (decision: 'APPROVED' | 'REJECTED') => {
    const confirmed = window.confirm(`Confirm final authority decision: ${decision}?`);
    if (!confirmed) return;
    const rationale = window.prompt('Enter the final decision rationale (required):');
    if (!rationale || !rationale.trim()) return;
    setActionLoading(true);
    try {
      await api.executeApplicationAction(applicationId, {
        action: 'FINALIZE_DECISION',
        decision_status: decision,
        reason: rationale.trim()
      });
      await loadApplication();
    } catch (err: any) {
      alert(err.message || 'Final decision failed');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading && !app) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-slate-500 text-sm">
          <Clock className="w-5 h-5 animate-spin text-blue-600" />
          <span>Opening Case Workbench...</span>
        </div>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="p-8 max-w-lg mx-auto">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0 text-red-600" />
          <span>{errorMsg}</span>
        </div>
        <button onClick={onBack} className="btn-secondary text-xs mt-4">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Applications</span>
        </button>
      </div>
    );
  }

  const permitted = app.permitted_actions || [];

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Case Header & Back Bar */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-xs text-slate-600 hover:text-slate-900 flex items-center gap-1.5 font-medium cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Applications Registry</span>
        </button>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500">Case Identifier:</span>
          <span className="font-mono font-bold text-sm text-blue-900 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
            {app.application_no}
          </span>
        </div>
      </div>

      {/* Case Workbench Summary Card */}
      <div className="portal-card p-6 border-t-4 border-t-blue-700 space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2.5">
              <Building2 className="w-5 h-5 text-blue-700" />
              <h1 className="text-lg font-bold text-slate-900">
                {app.institution?.name || app.institution_name}
              </h1>
            </div>
            <div className="text-xs text-slate-500 mt-1 flex flex-wrap gap-4 font-mono">
              <span>Code: {app.institution?.institution_code}</span>
              <span>•</span>
              <span>Region: {app.region_code || 'NORTHERN'}</span>
              <span>•</span>
              <span>Type: {app.application_type.replace(/_/g, ' ')}</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-[11px] text-slate-400 uppercase font-semibold">Current State</div>
              <div className="mt-0.5 flex items-center gap-2">
                <StatusBadge status={app.current_stage_code} />
                <StatusBadge status={app.workflow_status} />
                {app.workflow_status === 'STAGE_COMPLETED' && String(app.decision_status || '').startsWith('FINAL_') && (
                  <span className={`text-xs font-semibold px-2 py-1 rounded ${app.decision_status === 'FINAL_APPROVED' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                    Final outcome: {app.decision_status.replace('FINAL_', '')}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Workflow Progression Stepper */}
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
            Procedural Workflow Progression
          </div>
          <WorkflowStepper
            currentStage={app.current_stage_code}
            workflowStatus={app.workflow_status}
          />
        </div>

        {/* Contextual Permitted Actions Bar */}
        <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Authorized Stage Actions
            </div>
            <div className="text-xs text-slate-500">
              Current actor role ({user.role}) permitted transitions:
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5">
            {permitted.includes('SUBMIT') && (
              <button
                onClick={handleSubmitInitial}
                disabled={actionLoading}
                className="btn-primary text-xs"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Submit to Scrutiny Cell</span>
              </button>
            )}

            {permitted.includes('ADVANCE') && (
              <button
                onClick={handleAdvance}
                disabled={actionLoading}
                className="btn-primary text-xs bg-emerald-700 hover:bg-emerald-800"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Advance to Next Stage</span>
              </button>
            )}

            {permitted.includes('RETURN_DEFICIENCY') && (
              <button
                onClick={() => setShowDeficiencyModal(true)}
                disabled={actionLoading}
                className="btn-danger text-xs"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Return for Deficiency (Mandatory Reason)</span>
              </button>
            )}

            {permitted.includes('RESUBMIT') && (
              <button
                onClick={() => setShowResubmitModal(true)}
                disabled={actionLoading}
                className="btn-primary text-xs bg-amber-600 hover:bg-amber-700"
              >
                <Send className="w-3.5 h-3.5" />
                <span>Resubmit Deficiency Response</span>
              </button>
            )}

            {permitted.includes('RECOMMEND_DECISION') && (
              <>
                <button onClick={() => handleRecommendDecision('RECOMMENDED_APPROVAL')} disabled={actionLoading} className="btn-primary text-xs">
                  Recommend approval
                </button>
                <button onClick={() => handleRecommendDecision('RECOMMENDED_REJECTION')} disabled={actionLoading} className="btn-danger text-xs">
                  Recommend rejection
                </button>
              </>
            )}

            {permitted.includes('FINALIZE_DECISION') && (
              <>
                <button onClick={() => handleFinalDecision('APPROVED')} disabled={actionLoading} className="btn-primary text-xs">
                  Record final approval
                </button>
                <button onClick={() => handleFinalDecision('REJECTED')} disabled={actionLoading} className="btn-danger text-xs">
                  Record final rejection
                </button>
              </>
            )}

            {permitted.length === 0 && (
              <span className="text-xs text-slate-500 italic bg-white px-3 py-1.5 rounded border border-slate-200">
                No state transitions authorized for current role in this stage.
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Tabbed Workspace */}
      <div className="space-y-4">
        {/* Tab Headers */}
        <div className="flex border-b border-slate-200 space-x-2">
          <button
            onClick={() => setActiveTab('docs')}
            className={`pb-2.5 px-4 text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer border-b-2 flex items-center gap-2 ${
              activeTab === 'docs'
                ? 'border-blue-700 text-blue-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <FolderOpen className="w-4 h-4" />
            <span>Documents ({app.documents?.length || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab('compliance')}
            className={`pb-2.5 px-4 text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer border-b-2 flex items-center gap-2 ${
              activeTab === 'compliance'
                ? 'border-blue-700 text-blue-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <ShieldCheck className="w-4 h-4" />
            <span>Compliance obligations ({app.undertakings?.length || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab('evc')}
            className={`pb-2.5 px-4 text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer border-b-2 flex items-center gap-2 ${
              activeTab === 'evc'
                ? 'border-blue-700 text-blue-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <CalendarCheck className="w-4 h-4" />
            <span>EVC Inspection ({app.evc_events?.length || 0})</span>
          </button>

          <button
            onClick={() => setActiveTab('audit')}
            className={`pb-2.5 px-4 text-xs font-bold uppercase tracking-wider transition-colors cursor-pointer border-b-2 flex items-center gap-2 ${
              activeTab === 'audit'
                ? 'border-blue-700 text-blue-900'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Audit Journal ({app.events?.length || 0})</span>
          </button>
        </div>

        {/* Tab 1: Documents */}
        {activeTab === 'docs' && (
          <div className="portal-card p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-slate-900">Mandatory & Supporting Regulatory Documents</h3>
              {user.role === 'INSTITUTION_USER' && (
                <button
                  onClick={() => setShowUploadModal(true)}
                  className="btn-primary text-xs"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Upload New Document</span>
                </button>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="portal-table">
                <thead>
                  <tr>
                    <th>Document Name</th>
                    <th>Document Type</th>
                    <th>File Size</th>
                    <th>Expiry Date</th>
                    <th>Validity Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {app.documents?.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-xs text-slate-400">
                        No documents uploaded for this case.
                      </td>
                    </tr>
                  ) : (
                    app.documents?.map((doc: DocumentItem) => (
                      <tr key={doc.id}>
                        <td className="font-semibold text-xs text-slate-900 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                          <span>{doc.display_name}</span>
                        </td>
                        <td className="text-xs text-slate-600 font-mono">{doc.document_type}</td>
                        <td className="text-xs text-slate-500">{(doc.file_size / 1024).toFixed(1)} KB</td>
                        <td className="text-xs font-mono">{doc.expiry_date || 'N/A'}</td>
                        <td>
                          <StatusBadge status={doc.status} />
                        </td>
                        <td>
                          <button
                            type="button"
                            onClick={() => api.downloadDocument(doc.id).catch((err: any) => alert(err.message || 'Download failed'))}
                            className="btn-secondary text-xs py-1 px-2.5 inline-flex items-center gap-1"
                          >
                            <Download className="w-3 h-3" />
                            <span>Download</span>
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 2: Compliance Undertakings */}
        {activeTab === 'compliance' && (
          <div className="portal-card p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Time-Bound Institutional Commitments</h3>
            <div className="overflow-x-auto">
              <table className="portal-table">
                <thead>
                  <tr>
                    <th>Undertaking Requirement</th>
                    <th>Due Date</th>
                    <th>Status</th>
                    <th>Submitted Evidence</th>
                    <th>Official Verification</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {app.undertakings?.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-xs text-slate-400">
                        No undertakings bound to this case.
                      </td>
                    </tr>
                  ) : (
                    app.undertakings?.map((und: Undertaking) => (
                      <tr key={und.id}>
                        <td>
                          <div className="font-bold text-xs text-slate-900">{und.title}</div>
                          <div className="text-[11px] text-slate-500 mt-0.5">{und.description}</div>
                        </td>
                        <td className="text-xs font-mono text-slate-700">
                          {new Date(und.due_at).toLocaleDateString('en-IN', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric'
                          })}
                        </td>
                        <td>
                          <StatusBadge status={und.status} />
                        </td>
                        <td className="text-xs text-slate-700 max-w-xs">
                          {und.evidence_summary || <span className="text-slate-400 italic">No proof submitted yet</span>}
                        </td>
                        <td className="text-xs text-slate-700">
                          {und.verified_at ? (
                            <div>
                              <div className="font-semibold text-emerald-800">Verified by Officer</div>
                              <div className="text-[11px] text-slate-500">{und.verification_remarks}</div>
                            </div>
                          ) : (
                            <span className="text-slate-400 italic">Pending verification</span>
                          )}
                        </td>
                        <td>
                          {user.role in { REGIONAL_OFFICER: 1, BUREAU_OFFICER: 1, SYSTEM_ADMIN: 1 } && und.status === 'SUBMITTED' && (
                            <button
                              onClick={() => {
                                setSelectedUndId(und.id);
                                setShowVerifyUndModal(true);
                              }}
                              className="btn-primary text-xs py-1 px-2.5"
                            >
                              Verify
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: EVC Inspection */}
        {activeTab === 'evc' && (
          <div className="portal-card p-5 space-y-4">
            <h3 className="text-sm font-bold text-slate-900">Expert Visit Committee (EVC) Inspection Records</h3>
            {app.evc_events?.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-400">
                No EVC inspection scheduled for this application.
              </div>
            ) : (
              app.evc_events?.map((evc: EVCEvent) => (
                <div key={evc.id} className="p-4 rounded-lg border border-slate-200 bg-slate-50 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-slate-900">Inspection Event ID: {evc.id.substring(0, 8)}</span>
                    <StatusBadge status={evc.status} />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-500">Scheduled Visit Date:</span>
                      <span className="font-semibold text-slate-800 ml-2">
                        {evc.scheduled_date ? new Date(evc.scheduled_date).toLocaleString('en-IN') : 'Not Scheduled'}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Scheduling Deadline:</span>
                      <span className="font-semibold text-slate-800 ml-2">
                        {new Date(evc.scheduling_deadline).toLocaleDateString('en-IN')}
                      </span>
                    </div>
                  </div>
                  {evc.findings_summary && (
                    <div className="p-3 bg-white rounded border border-slate-200 text-xs text-slate-800">
                      <span className="font-bold block text-slate-600 mb-1">Committee Observations:</span>
                      {evc.findings_summary}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {/* Tab 4: Append-Only Audit Trail */}
        {activeTab === 'audit' && (
          <div className="portal-card p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900">Append-Only Case Audit Trail (Non-Repudiable)</h3>
              <span className="text-[11px] text-slate-400 font-mono">Immutable Journal</span>
            </div>

            <div className="space-y-3">
              {app.events?.map((ev: ApplicationEvent) => (
                <div
                  key={ev.id}
                  className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70 text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-blue-900 font-mono bg-blue-100 px-1.5 py-0.5 rounded">
                        {ev.action}
                      </span>
                      {ev.from_stage && ev.to_stage && (
                        <span className="text-slate-500">
                          ({ev.from_stage} → {ev.to_stage})
                        </span>
                      )}
                    </div>
                    <span className="text-slate-400 font-mono text-[11px]">
                      {new Date(ev.created_at).toLocaleString('en-IN')}
                    </span>
                  </div>

                  <div className="text-slate-700 font-medium">
                    Actor: {ev.actor_name || ev.actor_role}
                  </div>

                  {ev.reason && (
                    <div className="text-slate-600 bg-white p-2 rounded border border-slate-200 text-[11px] italic">
                      "{ev.reason}"
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Modal: Return Deficiency */}
      <Modal isOpen={showDeficiencyModal} onClose={() => setShowDeficiencyModal(false)} title="Issue Formal Deficiency Notice">
        <form onSubmit={handleReturnDeficiency} className="space-y-4">
          <div className="p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
            A detailed explanation of deficiencies is legally required before an application can be returned to an institution.
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Deficiency Justification & Required Documents *
            </label>
            <textarea
              required
              rows={4}
              value={deficiencyReason}
              onChange={e => setDeficiencyReason(e.target.value)}
              placeholder="Specify missing approvals, expired certificates, or physical infrastructure shortfalls..."
              className="w-full text-xs border border-slate-300 rounded p-2.5 focus:border-red-600 focus:outline-hidden"
            />
          </div>

          <div className="pt-3 border-t flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowDeficiencyModal(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="btn-danger text-xs"
            >
              {actionLoading ? 'Issuing...' : 'Return Application with Notice'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Resubmit */}
      <Modal isOpen={showResubmitModal} onClose={() => setShowResubmitModal(false)} title="Resubmit Application After Rectification">
        <form onSubmit={handleResubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Applicant Rectification Notes
            </label>
            <textarea
              rows={3}
              value={resubmitReason}
              onChange={e => setResubmitReason(e.target.value)}
              placeholder="Summarize revised documentation uploaded in response to the deficiency notice..."
              className="w-full text-xs border border-slate-300 rounded p-2.5 focus:border-blue-600 focus:outline-hidden"
            />
          </div>

          <div className="pt-3 border-t flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowResubmitModal(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="btn-primary text-xs"
            >
              {actionLoading ? 'Submitting...' : 'Confirm Resubmission'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Upload Document */}
      <Modal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} title="Upload Case Document">
        <form onSubmit={handleUploadDoc} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Select File (PDF, PNG, JPG)</label>
            <input
              type="file"
              required
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={e => setUploadFile(e.target.files ? e.target.files[0] : null)}
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Document Type</label>
            <select
              value={uploadDocType}
              onChange={e => setUploadDocType(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded p-2 bg-white"
            >
              <option value="LAND_LEASE_DEED">Registered Land Lease Deed</option>
              <option value="FIRE_NOC">State Fire & Safety Services NOC</option>
              <option value="BUILDING_STABILITY_CERT">Building Structural Stability Certificate</option>
              <option value="AICTE_AFFIDAVIT">Prescribed AICTE Affidavit</option>
              <option value="UNDERTAKING_EVIDENCE">Compliance Undertaking Evidence</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Registered Expiry Date (if applicable)
            </label>
            <input
              type="date"
              value={uploadExpiry}
              onChange={e => setUploadExpiry(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>

          <div className="pt-3 border-t flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowUploadModal(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading || !uploadFile}
              className="btn-primary text-xs"
            >
              {actionLoading ? 'Uploading...' : 'Save to Vault'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Verify Undertaking */}
      <Modal isOpen={showVerifyUndModal} onClose={() => setShowVerifyUndModal(false)} title="Official Undertaking Verification">
        <form onSubmit={handleVerifyUndertaking} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Verification Decision</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-1.5 text-xs text-slate-800">
                <input
                  type="radio"
                  checked={verifyApproved}
                  onChange={() => setVerifyApproved(true)}
                />
                <span className="font-semibold text-emerald-800">Approve & Verify Fulfillment</span>
              </label>
              <label className="flex items-center gap-1.5 text-xs text-slate-800">
                <input
                  type="radio"
                  checked={!verifyApproved}
                  onChange={() => setVerifyApproved(false)}
                />
                <span className="font-semibold text-red-800">Return for Correction</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Verification Remarks *</label>
            <textarea
              required
              rows={3}
              value={verifyRemarks}
              onChange={e => setVerifyRemarks(e.target.value)}
              placeholder="Record verification notes, equipment serial verification, or reasons for rejection..."
              className="w-full text-xs border border-slate-300 rounded p-2.5 focus:border-blue-600 focus:outline-hidden"
            />
          </div>

          <div className="pt-3 border-t flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowVerifyUndModal(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="btn-primary text-xs"
            >
              {actionLoading ? 'Saving...' : 'Record Verification'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
