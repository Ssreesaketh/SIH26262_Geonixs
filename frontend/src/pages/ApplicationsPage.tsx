import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Application, User, WorkflowTemplate } from '../types';
import { Search, Filter, Plus, ArrowUpRight, Clock, AlertCircle } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface ApplicationsPageProps {
  user: User;
  initialStageFilter?: string;
  onSelectApplication: (id: string) => void;
}

export const ApplicationsPage: React.FC<ApplicationsPageProps> = ({
  user,
  initialStageFilter,
  onSelectApplication
}) => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState(initialStageFilter || '');
  const [statusFilter, setStatusFilter] = useState('');
  const [total, setTotal] = useState(0);

  // New Application Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [appType, setAppType] = useState('EXTENSION_OF_APPROVAL');
  const [wfCode, setWfCode] = useState('SCRUTINY_EVC');
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const loadApplications = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const data = await api.listApplications({
        search: search || undefined,
        stage: stageFilter || undefined,
        status: statusFilter || undefined,
        pageSize: 50
      });
      setApplications(data.items);
      setTotal(data.total);
    } catch (err: any) {
      console.error('Failed to load applications:', err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadApplications();
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void loadApplications(false);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [stageFilter, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadApplications();
  };

  const handleCreateApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user.institution_id && user.role !== 'SYSTEM_ADMIN') {
      setCreateError('You must be associated with an institution to create an application.');
      return;
    }
    setCreateLoading(true);
    setCreateError(null);
    try {
      const created = await api.createApplication({
        institution_id: user.institution_id || 'sample-inst-id',
        application_type: appType,
        workflow_template_code: wfCode
      });
      setShowCreateModal(false);
      onSelectApplication(created.id);
    } catch (err: any) {
      setCreateError(err.message || 'Failed to create application');
    } finally {
      setCreateLoading(false);
    }
  };

  const calculateSlaRemaining = (dueAtStr: string) => {
    const due = new Date(dueAtStr).getTime();
    const now = Date.now();
    const diff = due - now;

    if (diff < 0) {
      const days = Math.abs(Math.floor(diff / (1000 * 60 * 60 * 24)));
      const hrs = Math.abs(Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)));
      return {
        text: `Overdue by ${days}d ${hrs}h`,
        isOverdue: true,
        isWarning: false
      };
    } else {
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hrs = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      return {
        text: `${days}d ${hrs}h remaining`,
        isOverdue: false,
        isWarning: diff < 48 * 60 * 60 * 1000
      };
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">Applications</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            End-to-end technical institution approval cases, current stages & SLA countdowns
          </p>
          <p className="text-[11px] text-emerald-700 mt-2">● Live sync · new submissions and officer decisions appear automatically</p>
        </div>

        {user.role === 'INSTITUTION_USER' && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary text-xs cursor-pointer shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>New Application Draft</span>
          </button>
        )}
      </div>

      {/* Filter and Search Bar */}
      <div className="portal-card p-4 flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex-1 w-full flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by Application No, College Name or Code..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full text-xs pl-9 pr-3 py-2 border border-slate-300 rounded-md focus:border-blue-600 focus:outline-hidden"
            />
          </div>
          <button type="submit" className="btn-secondary text-xs py-2 px-3">
            Search
          </button>
        </form>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <select
            value={stageFilter}
            onChange={e => setStageFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-md py-2 px-2.5 bg-white text-slate-700 focus:outline-hidden"
          >
            <option value="">All Stages</option>
            <option value="DRAFT">Draft</option>
            <option value="SCRUTINY">Scrutiny Review</option>
            <option value="EVC">EVC Inspection</option>
            <option value="SAC_SHC">SAC / SHC Committee</option>
            <option value="COMPLETED">Completed</option>
          </select>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-md py-2 px-2.5 bg-white text-slate-700 focus:outline-hidden"
          >
            <option value="">All Statuses</option>
            <option value="UNDER_REVIEW">Under Review</option>
            <option value="DEFICIENCY_RETURNED">Deficiency Returned</option>
            <option value="STAGE_COMPLETED">Stage Completed</option>
          </select>
        </div>
      </div>

      {/* Applications Table */}
      <div className="portal-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="portal-table">
            <thead>
              <tr>
                <th>Application No</th>
                {user.role !== 'INSTITUTION_USER' && <th>Institution Name</th>}
                <th>Type</th>
                <th>Current Stage</th>
                <th>Status</th>
                {user.role !== 'INSTITUTION_USER' && <th>SLA Due Date</th>}
                {user.role !== 'INSTITUTION_USER' && <th>Assigned Role</th>}
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={user.role === 'INSTITUTION_USER' ? 5 : 8} className="py-8 text-center text-xs text-slate-400">
                    Loading applications...
                  </td>
                </tr>
              ) : applications.length === 0 ? (
                <tr>
                  <td colSpan={user.role === 'INSTITUTION_USER' ? 5 : 8} className="py-8 text-center text-xs text-slate-400">
                    No applications found matching search criteria.
                  </td>
                </tr>
              ) : (
                applications.map(app => {
                  const sla = calculateSlaRemaining(app.stage_due_at);
                  return (
                    <tr key={app.id} className="hover:bg-blue-50/40 transition-colors">
                      <td className="font-mono font-bold text-blue-900 text-xs">
                        {app.application_no}
                      </td>
                      {user.role !== 'INSTITUTION_USER' && (
                        <td>
                          <div className="font-semibold text-slate-900 text-xs">{app.institution_name}</div>
                          <div className="text-[11px] text-slate-500 font-mono">Region: {app.region_code}</div>
                        </td>
                      )}
                      <td className="text-xs text-slate-600">
                        {app.application_type.replace(/_/g, ' ')}
                      </td>
                      <td>
                        <span className="font-semibold text-xs text-slate-800">
                          {app.current_stage_code}
                        </span>
                      </td>
                      <td>
                        <StatusBadge status={app.workflow_status} />
                        {user.role === 'INSTITUTION_USER' && app.workflow_status === 'STAGE_COMPLETED' && String(app.decision_status || '').startsWith('FINAL_') && (
                          <div className={`text-[10px] font-semibold mt-1 ${app.decision_status === 'FINAL_APPROVED' ? 'text-emerald-700' : 'text-red-700'}`}>
                            Final outcome: {app.decision_status.replace('FINAL_', '')}
                          </div>
                        )}
                      </td>
                      {user.role !== 'INSTITUTION_USER' && (
                        <>
                          <td>
                            <div className="text-xs font-medium text-slate-800">
                              {new Date(app.stage_due_at).toLocaleDateString('en-IN', {
                                day: '2-digit',
                                month: 'short',
                                year: 'numeric'
                              })}
                            </div>
                            <span
                              className={`text-[10px] font-semibold inline-flex items-center gap-1 ${
                                sla.isOverdue
                                  ? 'text-red-700 bg-red-100 px-1 rounded'
                                  : sla.isWarning
                                  ? 'text-amber-700 bg-amber-100 px-1 rounded'
                                  : 'text-slate-500'
                              }`}
                            >
                              <Clock className="w-2.5 h-2.5" />
                              <span>{sla.text}</span>
                            </span>
                          </td>
                          <td className="text-xs text-slate-600 font-mono">{app.assigned_role}</td>
                        </>
                      )}
                      <td>
                        <button
                          onClick={() => onSelectApplication(app.id)}
                          className="btn-primary text-xs py-1 px-2.5 font-normal"
                        >
                          <span>Open Case</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Create Application */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="Create New Application Draft">
        <form onSubmit={handleCreateApplication} className="space-y-4">
          {createError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded text-xs text-red-800 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{createError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Application Type</label>
            <select
              value={appType}
              onChange={e => setAppType(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded px-3 py-2 bg-white"
            >
              <option value="EXTENSION_OF_APPROVAL">Extension of Approval (EoA)</option>
              <option value="NEW_INSTITUTION">New Technical Institution</option>
              <option value="INTAKE_VARIATION">Intake Variation / Course Addition</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Configured Workflow Route</label>
            <select
              value={wfCode}
              onChange={e => setWfCode(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded px-3 py-2 bg-white"
            >
              <option value="SCRUTINY_EVC">Scrutiny + EVC + Hearing Committee (Standard)</option>
              <option value="ONLY_SCRUTINY">Only Scrutiny (Routine Fast-Track)</option>
              <option value="EVC_SAC_SHC">Special Inspection & Hearing Route</option>
            </select>
          </div>

          <div className="pt-3 border-t flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createLoading}
              className="btn-primary text-xs"
            >
              {createLoading ? 'Creating...' : 'Initialize Case'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
