import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Application, DocumentItem, User } from '../types';
import { FolderLock, Upload, RefreshCw, Download, AlertTriangle, FileText, CheckCircle2, Sparkles, LoaderCircle } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface DocumentsPageProps {
  user: User;
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({ user }) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [forms, setForms] = useState<Array<{ key: string; title: string; description: string; filename: string; audience: string; download_url: string }>>([]);
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');

  // Renew Modal
  const [showRenewModal, setShowRenewModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);
  const [renewFile, setRenewFile] = useState<File | null>(null);
  const [renewExpiry, setRenewExpiry] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [evaluatingDocId, setEvaluatingDocId] = useState<string | null>(null);
  const [evaluationReport, setEvaluationReport] = useState<any | null>(null);

  // Upload Modal
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDocType, setUploadDocType] = useState('LAND_LEASE_DEED');
  const [uploadDisplayName, setUploadDisplayName] = useState('');
  const [uploadExpiry, setUploadExpiry] = useState('');
  const [uploadApplicationId, setUploadApplicationId] = useState('');
  const [uploadCorrectionOfId, setUploadCorrectionOfId] = useState('');

  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [data, formData, appData] = await Promise.all([
        api.listDocuments(statusFilter || undefined),
        api.listForms(),
        user.role === 'INSTITUTION_USER' ? api.listApplications({ page: 1, pageSize: 100 }) : Promise.resolve({ items: [], total: 0, page: 1, page_size: 100 })
      ]);
      setDocuments(data);
      setForms(formData);
      setApplications(appData.items);
    } catch (err: any) {
      console.error('Failed to load documents:', err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void loadData(false);
    }, 8000);
    return () => window.clearInterval(timer);
  }, [statusFilter]);

  const handleRenew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (renewFile && renewFile.size > 10 * 1024 * 1024) { alert('Maximum file size is 10 MB.'); return; }
    if (!selectedDoc || !renewFile || !renewExpiry) {
      alert('Please select a file and provide the new registered expiry date.');
      return;
    }
    setActionLoading(true);
    try {
      const fd = new FormData();
      fd.append('file', renewFile);
      fd.append('new_expiry_date', renewExpiry);
      await api.renewDocument(selectedDoc.id, fd);
      setShowRenewModal(false);
      setSelectedDoc(null);
      setRenewFile(null);
      setRenewExpiry('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Renewal failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUploadNew = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;
    if (uploadFile.size > 10 * 1024 * 1024) { alert('Maximum file size is 10 MB.'); return; }
    setActionLoading(true);
    try {
      const fd = new FormData();
      fd.append('file', uploadFile);
      fd.append('document_type', uploadDocType);
      if (uploadDisplayName) fd.append('display_name', uploadDisplayName);
      if (uploadExpiry) fd.append('expiry_date_str', uploadExpiry);
      if (uploadApplicationId) fd.append('application_id', uploadApplicationId);
      if (uploadCorrectionOfId) fd.append('renewal_of_id', uploadCorrectionOfId);
      if (user.institution_id) fd.append('institution_id', user.institution_id);

      await api.uploadDocument(fd);
      setShowUploadModal(false);
      setUploadFile(null);
      setUploadDisplayName('');
      setUploadExpiry('');
      setUploadApplicationId('');
      setUploadCorrectionOfId('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Upload failed');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <FolderLock className="w-5 h-5 text-blue-700" />
            <span>{user.role === 'INSTITUTION_USER' ? 'Forms & documents' : 'Documents & forms'}</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {user.role === 'INSTITUTION_USER'
              ? 'Download the forms for your institution, manage your own documents and track validity.'
              : 'Review institution evidence and access role-specific working templates.'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-md py-2 px-3 bg-white text-slate-700"
          >
            <option value="">All Statuses</option>
            <option value="EXPIRING_SOON">Expiring Soon (30 Days)</option>
            <option value="EXPIRED">Expired</option>
            <option value="SUBMITTED">Awaiting review</option>
            <option value="VERIFIED">Verified</option>
            <option value="RETURNED_FOR_CORRECTION">Correction required</option>
            <option value="VALID">Valid / expiry tracked</option>
            <option value="SUPERSEDED">Superseded (Historic)</option>
          </select>

          {user.role === 'INSTITUTION_USER' && (
            <button
              onClick={() => { setUploadCorrectionOfId(''); setUploadApplicationId(''); setShowUploadModal(true); }}
              className="btn-primary text-xs"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Upload Document</span>
            </button>
          )}
        </div>
      </div>

      <section className="portal-card p-5 space-y-3">
        <div>
          <h2 className="text-sm font-bold text-slate-900">Downloadable forms and templates</h2>
          <p className="text-xs text-slate-500 mt-1">Files download directly from the authenticated service. Templates are demonstration aids, not official statutory forms.</p>
        </div>
        {forms.length === 0 ? (
          <p className="text-xs text-slate-500 py-3">No forms are available for this role.</p>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {forms.map(form => (
              <div key={form.key} className="flex items-start justify-between gap-3 border border-slate-200 rounded-lg p-4">
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-slate-900">{form.title}</div>
                  <p className="text-xs text-slate-500 mt-1">{form.description}</p>
                  <div className="text-[10px] text-slate-400 mt-2 uppercase tracking-wide">{form.audience} template · PDF</div>
                </div>
                <button
                  type="button"
                  onClick={() => api.downloadForm(form.key).catch((err: any) => alert(err.message || 'Form download failed'))}
                  className="btn-primary text-xs shrink-0"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      <div className="portal-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="portal-table">
            <thead>
              <tr>
                <th>Document Name & Title</th>
                <th>Type</th>
                <th>Registered Expiry</th>
                <th>Status</th>
                <th>Submission Date</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-slate-400">
                    Loading document vault...
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-slate-400">
                    No documents found.
                  </td>
                </tr>
              ) : (
                documents.map(doc => {
                  const isExpiring = doc.status === 'EXPIRING_SOON';
                  const isExpired = doc.status === 'EXPIRED';

                  return (
                    <tr key={doc.id} className={isExpired ? 'bg-red-50/30' : isExpiring ? 'bg-amber-50/20' : ''}>
                      <td>
                        <div className="font-bold text-xs text-slate-900 flex items-center gap-2">
                          <FileText className="w-4 h-4 text-blue-600 shrink-0" />
                          <span>{doc.display_name}</span>
                        </div>
                        {doc.renewal_of_id && (
                          <div className="text-[10px] text-blue-700 font-mono mt-0.5">
                            Renewal of Doc: {doc.renewal_of_id.substring(0, 8)}...
                          </div>
                        )}
                      </td>
                      <td className="text-xs font-mono text-slate-700">{doc.document_type}</td>
                      <td className="text-xs font-mono font-semibold">
                        {doc.expiry_date ? (
                          <span className={isExpired ? 'text-red-700' : isExpiring ? 'text-amber-700' : 'text-slate-800'}>
                            {doc.expiry_date}
                          </span>
                        ) : (
                          <span className="text-slate-400 font-normal">Perpetual / N/A</span>
                        )}
                      </td>
                      <td>
                        <StatusBadge status={doc.status} />
                      </td>
                      <td className="text-xs font-mono text-slate-500">
                        {new Date(doc.submitted_at).toLocaleDateString('en-IN')}
                        {doc.verification_remarks && <p className="max-w-52 whitespace-normal text-[10px] text-amber-700 mt-1">Review: {doc.verification_remarks}</p>}
                      </td>
                      <td>
                        <div className="flex flex-wrap items-center gap-2 min-w-[260px]">
                          {doc.mime_type === 'application/pdf' && (
                            <button type="button" disabled={evaluatingDocId === doc.id} onClick={async () => {
                              setEvaluatingDocId(doc.id);
                              try { const result = await api.evaluateDocument(doc.id); setEvaluationReport(result); }
                              catch (err: any) { alert(err.message || 'PDF evaluation failed'); }
                              finally { setEvaluatingDocId(null); }
                            }} className="btn-secondary text-xs py-1 px-2.5 inline-flex items-center gap-1" title="Run advisory PDF evaluation">
                              {evaluatingDocId === doc.id ? <LoaderCircle className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                              <span>{evaluatingDocId === doc.id ? 'Evaluating…' : 'AI review'}</span>
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => api.downloadDocument(doc.id).catch((err: any) => alert(err.message || 'Download failed'))}
                            className="btn-secondary text-xs py-1 px-2.5 inline-flex items-center gap-1"
                          >
                            <Download className="w-3 h-3" />
                            <span>Download</span>
                          </button>

                          {user.role !== 'INSTITUTION_USER' && ['SUBMITTED', 'RETURNED_FOR_CORRECTION'].includes(doc.status) && (
                            <>
                              <button type="button" onClick={async () => {
                                const remarks = window.prompt('Verification remarks (required):');
                                if (!remarks || remarks.trim().length < 3) return;
                                try { await api.reviewDocument(doc.id, 'VERIFIED', remarks.trim()); await loadData(); }
                                catch (err: any) { alert(err.message || 'Review failed'); }
                              }} className="btn-primary text-xs py-1 px-2">Verify</button>
                              <button type="button" onClick={async () => {
                                const remarks = window.prompt('Explain what must be corrected (required):');
                                if (!remarks || remarks.trim().length < 3) return;
                                try { await api.reviewDocument(doc.id, 'RETURNED_FOR_CORRECTION', remarks.trim()); await loadData(); }
                                catch (err: any) { alert(err.message || 'Review failed'); }
                              }} className="btn-secondary text-xs py-1 px-2">Request correction</button>
                            </>
                          )}
                          {user.role === 'INSTITUTION_USER' && doc.status === 'RETURNED_FOR_CORRECTION' && (
                            <button type="button" onClick={() => {
                              setUploadDocType(doc.document_type);
                              setUploadApplicationId(doc.application_id || '');
                              setUploadCorrectionOfId(doc.id);
                              setShowUploadModal(true);
                            }} className="btn-primary text-xs py-1 px-2.5">Upload correction</button>
                          )}
                          {user.role === 'INSTITUTION_USER' && (isExpired || isExpiring) && (
                            <button
                              onClick={() => {
                                setSelectedDoc(doc);
                                setShowRenewModal(true);
                              }}
                              className="btn-primary text-xs py-1 px-2.5 bg-amber-600 hover:bg-amber-700"
                            >
                              <RefreshCw className="w-3 h-3" />
                              <span>Renew</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Renew Document */}
      <Modal isOpen={showRenewModal} onClose={() => setShowRenewModal(false)} title="Renew Expiring / Expired Document">
        <form onSubmit={handleRenew} className="space-y-4">
          <div className="p-3 bg-blue-50 border border-blue-200 rounded text-xs text-blue-800">
            Renewing preserves the historical document record ({selectedDoc?.display_name}) with status "SUPERSEDED" while creating a linked renewed document.
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Select Renewed Document (PDF, PNG, JPG) *
            </label>
            <input
              type="file"
              required
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={e => { const file = e.target.files?.[0] || null; if (file && file.size > 10 * 1024 * 1024) { alert('Maximum file size is 10 MB.'); e.currentTarget.value = ''; setRenewFile(null); } else setRenewFile(file); }}
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              New Registered Expiry Date *
            </label>
            <input
              type="date"
              required
              value={renewExpiry}
              onChange={e => setRenewExpiry(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>

          <div className="pt-3 border-t flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowRenewModal(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="btn-primary text-xs"
            >
              {actionLoading ? 'Uploading...' : 'Confirm Document Renewal'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: AI evaluation report */}
      <Modal isOpen={!!evaluationReport} onClose={() => setEvaluationReport(null)} title="AI-assisted PDF evaluation">
        {evaluationReport && <div className="space-y-4">
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900">
            Advisory report only. This does not verify the document, determine legal compliance, or advance/reject an application.
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="rounded border border-slate-200 p-3"><div className="text-slate-500">Processing mode</div><div className="font-semibold mt-1">{String(evaluationReport.engine_mode || 'unknown').replace(/_/g, ' ')}</div></div>
            <div className="rounded border border-slate-200 p-3"><div className="text-slate-500">Pages / extracted chars</div><div className="font-semibold mt-1">{evaluationReport.report?.page_count ?? '—'} / {evaluationReport.report?.text_character_count ?? '—'}</div></div>
          </div>
          <div><h4 className="text-xs font-bold text-slate-800 mb-1">Summary</h4><p className="text-xs leading-5 text-slate-700">{evaluationReport.report?.summary}</p></div>
          {!!evaluationReport.report?.findings?.length && <div className="space-y-2"><h4 className="text-xs font-bold text-slate-800">Findings</h4>{evaluationReport.report.findings.map((finding: any, i: number) => <div key={`${finding.title}-${i}`} className="rounded-md border border-slate-200 p-3"><div className="flex items-start justify-between gap-2"><div className="text-xs font-semibold text-slate-900">{finding.title}</div><span className="text-[10px] uppercase rounded bg-slate-100 px-2 py-1">{finding.severity}</span></div><p className="text-xs text-slate-600 mt-1 leading-5">{finding.details}</p>{finding.evidence?.map((ev: any, j: number) => <p key={j} className="text-[11px] text-slate-500 mt-1">{ev.page ? `Page ${ev.page}: ` : ''}{ev.quote || ''}</p>)}</div>)}</div>}
          {!!evaluationReport.report?.limitations?.length && <div><h4 className="text-xs font-bold text-slate-800 mb-1">Limitations</h4><ul className="list-disc pl-5 space-y-1">{evaluationReport.report.limitations.map((x: string, i: number) => <li key={i} className="text-xs text-slate-600">{x}</li>)}</ul></div>}
          {!!evaluationReport.report?.retrieved_sources?.length && <div><h4 className="text-xs font-bold text-slate-800 mb-1">Retrieved regulatory sources</h4>{evaluationReport.report.retrieved_sources.map((source: any, i: number) => <p key={i} className="text-xs text-slate-600">{source.title}{source.page ? ` · page ${source.page}` : ''}{source.version ? ` · ${source.version}` : ''}</p>)}</div>}
        </div>}
      </Modal>

      {/* Modal: Upload New Document */}
      <Modal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} title="Upload Regulatory Document">
        <form onSubmit={handleUploadNew} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Select File (PDF, PNG, JPG) *</label>
            <input
              type="file"
              required
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={e => { const file = e.target.files?.[0] || null; if (file && file.size > 10 * 1024 * 1024) { alert('Maximum file size is 10 MB.'); e.currentTarget.value = ''; setUploadFile(null); } else setUploadFile(file); }}
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Application (optional but recommended)</label>
            <select value={uploadApplicationId} onChange={e => setUploadApplicationId(e.target.value)} className="w-full text-xs border border-slate-300 rounded p-2 bg-white">
              <option value="">Institution-level document (not tied to an application)</option>
              {applications.map(app => <option key={app.id} value={app.id}>{app.application_no} — {app.application_type} — {app.current_stage_code}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Document Type *</label>
            <select
              value={uploadDocType}
              onChange={e => setUploadDocType(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded p-2 bg-white"
            >
              <option value="LAND_LEASE_DEED">Registered Land Lease Deed</option>
              <option value="FIRE_NOC">State Fire & Safety Services NOC</option>
              <option value="BUILDING_STABILITY_CERT">Building Structural Stability Certificate</option>
              <option value="AICTE_AFFIDAVIT">Prescribed AICTE Affidavit</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Display Title</label>
            <input
              type="text"
              placeholder="e.g. Registered 30-Year Land Deed (Plot 14-B)"
              value={uploadDisplayName}
              onChange={e => setUploadDisplayName(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Registered Expiry Date</label>
            <input
              type="date"
              value={uploadExpiry}
              onChange={e => setUploadExpiry(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>

          <p className="text-[11px] text-slate-500">Allowed: PDF, JPG/JPEG, PNG. Maximum 10 MB per file. Uploads remain “Awaiting review” until an authorized officer verifies them or requests corrections.</p>
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
    </div>
  );
};
