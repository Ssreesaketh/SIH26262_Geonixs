import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Undertaking, User } from '../types';
import { ShieldCheck, Clock, CheckCircle2, AlertTriangle, Send } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface CompliancePageProps {
  user: User;
  onOpenCase: (id: string) => void;
}

export const CompliancePage: React.FC<CompliancePageProps> = ({ user, onOpenCase }) => {
  const [undertakings, setUndertakings] = useState<Undertaking[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  // Submit Evidence Modal
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [selectedUndId, setSelectedUndId] = useState<string | null>(null);
  const [evidenceSummary, setEvidenceSummary] = useState('');

  // Verify Modal
  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [verifyApproved, setVerifyApproved] = useState(true);
  const [verifyRemarks, setVerifyRemarks] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const data = await api.listCompliance(filter || undefined);
      setUndertakings(data);
    } catch (err: any) {
      console.error('Failed to load undertakings:', err);
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
  }, [filter]);

  const handleSubmitEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUndId || !evidenceSummary.trim()) return;
    setActionLoading(true);
    try {
      await api.submitUndertakingEvidence(selectedUndId, evidenceSummary.trim());
      setShowSubmitModal(false);
      setSelectedUndId(null);
      setEvidenceSummary('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Evidence submission failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUndId) return;
    setActionLoading(true);
    try {
      await api.verifyUndertaking(selectedUndId, verifyApproved, verifyRemarks);
      setShowVerifyModal(false);
      setSelectedUndId(null);
      setVerifyRemarks('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600" />
            <span>Institutional compliance</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Track time-bound commitments, evidence submissions and verification status.
          </p>
        </div>

        <select
          value={filter}
          onChange={e => setFilter(e.target.value)}
          className="text-xs border border-slate-300 rounded-md py-2 px-3 bg-white text-slate-700 focus:outline-hidden"
        >
          <option value="">All Obligations</option>
          <option value="PENDING">Pending Submission</option>
          <option value="SUBMITTED">Submitted (Awaiting Verification)</option>
          <option value="VERIFIED">Verified & Closed</option>
          <option value="RETURNED_FOR_CORRECTION">Returned for Correction</option>
        </select>
      </div>

      <div className="portal-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="portal-table">
            <thead>
              <tr>
                <th>Commitment Title & Scope</th>
                <th>Due Date</th>
                <th>Fulfillment Status</th>
                <th>Submitted Evidence</th>
                <th>Verification Audit</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-slate-400">
                    Loading compliance records...
                  </td>
                </tr>
              ) : undertakings.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-slate-400">
                    No compliance undertakings found matching criteria.
                  </td>
                </tr>
              ) : (
                undertakings.map(und => {
                  const isOverdue = new Date(und.due_at).getTime() < Date.now() && und.status !== 'VERIFIED';
                  return (
                    <tr key={und.id}>
                      <td>
                        <div className="font-bold text-xs text-slate-900">{und.title}</div>
                        <div className="text-[11px] text-slate-500 mt-0.5 max-w-md">{und.description}</div>
                      </td>
                      <td className="text-xs font-mono">
                        <div className="font-semibold text-slate-800">
                          {new Date(und.due_at).toLocaleDateString('en-IN', {
                            day: '2-digit',
                            month: 'short',
                            year: 'numeric'
                          })}
                        </div>
                        {isOverdue && (
                          <span className="text-[10px] text-red-700 bg-red-100 font-bold px-1.5 py-0.2 rounded inline-block mt-0.5">
                            Overdue
                          </span>
                        )}
                      </td>
                      <td>
                        <StatusBadge status={und.status} />
                      </td>
                      <td className="text-xs text-slate-700 max-w-xs">
                        {und.evidence_summary || <span className="text-slate-400 italic">No proof submitted</span>}
                      </td>
                      <td className="text-xs text-slate-600">
                        {und.verified_at ? (
                          <div>
                            <span className="font-semibold text-emerald-700">Verified</span>
                            <div className="text-[11px] text-slate-500">{und.verification_remarks}</div>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">Unverified</span>
                        )}
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          {user.role === 'INSTITUTION_USER' && und.status in { PENDING: 1, RETURNED_FOR_CORRECTION: 1 } && (
                            <button
                              onClick={() => {
                                setSelectedUndId(und.id);
                                setShowSubmitModal(true);
                              }}
                              className="btn-primary text-xs py-1 px-2.5"
                            >
                              <Send className="w-3 h-3" />
                              <span>Submit Proof</span>
                            </button>
                          )}

                          {user.role in { REGIONAL_OFFICER: 1, BUREAU_OFFICER: 1, SYSTEM_ADMIN: 1 } && und.status === 'SUBMITTED' && (
                            <button
                              onClick={() => {
                                setSelectedUndId(und.id);
                                setShowVerifyModal(true);
                              }}
                              className="btn-primary text-xs py-1 px-2.5 bg-emerald-700 hover:bg-emerald-800"
                            >
                              <CheckCircle2 className="w-3 h-3" />
                              <span>Verify</span>
                            </button>
                          )}

                          <button
                            onClick={() => onOpenCase(und.application_id)}
                            className="btn-secondary text-xs py-1 px-2"
                          >
                            Case
                          </button>
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

      {/* Modal: Submit Evidence */}
      <Modal isOpen={showSubmitModal} onClose={() => setShowSubmitModal(false)} title="Submit Compliance Proof">
        <form onSubmit={handleSubmitEvidence} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Evidence Summary & Equipment / Recruitment Details *
            </label>
            <textarea
              required
              rows={4}
              value={evidenceSummary}
              onChange={e => setEvidenceSummary(e.target.value)}
              placeholder="State invoices, appointment order numbers, municipal receipts, and photo attachments..."
              className="w-full text-xs border border-slate-300 rounded p-2.5"
            />
          </div>

          <div className="pt-3 border-t flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowSubmitModal(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="btn-primary text-xs"
            >
              {actionLoading ? 'Submitting...' : 'Submit to Regional Officer'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Modal: Verify Undertaking */}
      <Modal isOpen={showVerifyModal} onClose={() => setShowVerifyModal(false)} title="Official Compliance Verification">
        <form onSubmit={handleVerify} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Official Decision</label>
            <div className="flex gap-4">
              <label className="flex items-center gap-1.5 text-xs text-slate-800 cursor-pointer">
                <input
                  type="radio"
                  checked={verifyApproved}
                  onChange={() => setVerifyApproved(true)}
                />
                <span className="font-semibold text-emerald-800">Approve & Mark Verified</span>
              </label>
              <label className="flex items-center gap-1.5 text-xs text-slate-800 cursor-pointer">
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
            <label className="block text-xs font-semibold text-slate-700 mb-1">Officer Remarks *</label>
            <textarea
              required
              rows={3}
              value={verifyRemarks}
              onChange={e => setVerifyRemarks(e.target.value)}
              placeholder="Enter official observation, serial numbers checked, or correction requirements..."
              className="w-full text-xs border border-slate-300 rounded p-2.5"
            />
          </div>

          <div className="pt-3 border-t flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowVerifyModal(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="btn-primary text-xs"
            >
              {actionLoading ? 'Recording...' : 'Record Verification'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
