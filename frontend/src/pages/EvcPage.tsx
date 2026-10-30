import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { EVCEvent, User } from '../types';
import { CalendarCheck, Clock, CheckCircle, FileText, CalendarPlus } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { Modal } from '../components/Modal';

interface EvcPageProps {
  user: User;
  onOpenCase: (id: string) => void;
}

export const EvcPage: React.FC<EvcPageProps> = ({ user, onOpenCase }) => {
  const [events, setEvents] = useState<EVCEvent[]>([]);
  const [loading, setLoading] = useState(true);

  // Complete Findings Modal
  const [showFindingsModal, setShowFindingsModal] = useState(false);
  const [selectedEvcId, setSelectedEvcId] = useState<string | null>(null);
  const [findingsSummary, setFindingsSummary] = useState('');
  const [outcome, setOutcome] = useState('RECOMMENDED');
  const [actionLoading, setActionLoading] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [scheduleApplicationId, setScheduleApplicationId] = useState<string | null>(null);
  const [scheduledDate, setScheduledDate] = useState('');
  const [inspectionMode, setInspectionMode] = useState('PHYSICAL_VISIT');
  const [inspectionVenue, setInspectionVenue] = useState('');

  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const data = await api.listEvc();
      setEvents(data);
    } catch (err: any) {
      console.error('Failed to load EVC schedules:', err);
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
  }, []);

  const handleScheduleInspection = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scheduleApplicationId || !scheduledDate) return;
    setActionLoading(true);
    try {
      await api.scheduleEvc(scheduleApplicationId, {
        scheduled_date: new Date(scheduledDate).toISOString(),
        committee_details: {
          recommended_mode: inspectionMode,
          venue: inspectionVenue.trim() || 'Institution campus'
        }
      });
      setShowScheduleModal(false);
      setScheduleApplicationId(null);
      setScheduledDate('');
      setInspectionVenue('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to schedule inspection');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCompleteFindings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvcId || !findingsSummary.trim()) return;
    setActionLoading(true);
    try {
      await api.completeEvc(selectedEvcId, {
        findings_summary: findingsSummary.trim(),
        outcome
      });
      setShowFindingsModal(false);
      setSelectedEvcId(null);
      setFindingsSummary('');
      await loadData();
    } catch (err: any) {
      alert(err.message || 'Failed to submit findings');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <CalendarCheck className="w-5 h-5 text-indigo-600" />
            <span>EVC schedule</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Schedule visits, monitor timelines and record authorized outcomes.
          </p>
        </div>
      </div>

      <div className="portal-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="portal-table">
            <thead>
              <tr>
                <th>Inspection Event</th>
                <th>Status</th>
                <th>Scheduled Date</th>
                <th>Scheduling Deadline</th>
                <th>Committee Details</th>
                <th>Findings Summary</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-xs text-slate-400">
                    Loading EVC inspection pipeline...
                  </td>
                </tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-xs text-slate-400">
                    No EVC inspections currently queued.
                  </td>
                </tr>
              ) : (
                events.map(evc => (
                  <tr key={evc.id}>
                    <td>
                      <button
                        onClick={() => onOpenCase(evc.application_id)}
                        className="font-mono text-xs font-bold text-blue-700 hover:underline"
                      >
                        App Case: {evc.application_id.substring(0, 8)}...
                      </button>
                    </td>
                    <td>
                      <StatusBadge status={evc.status} />
                    </td>
                    <td className="text-xs font-medium text-slate-800">
                      {evc.scheduled_date ? new Date(evc.scheduled_date).toLocaleString('en-IN') : (
                        <span className="text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                          Unscheduled
                        </span>
                      )}
                    </td>
                    <td className="text-xs font-mono text-slate-600">
                      {new Date(evc.scheduling_deadline).toLocaleDateString('en-IN')}
                    </td>
                    <td className="text-xs text-slate-600">
                      {evc.committee_details?.recommended_mode || 'Physical Inspection'}
                    </td>
                    <td className="text-xs text-slate-700 max-w-xs">
                      {evc.findings_summary ? (
                        <span className="line-clamp-2">{evc.findings_summary}</span>
                      ) : (
                        <span className="text-slate-400 italic">Pending visit</span>
                      )}
                    </td>
                    <td>
                      {(user.role === 'REGIONAL_OFFICER' || user.role === 'SYSTEM_ADMIN') && evc.status === 'PENDING_SCHEDULE' && (
                        <button
                          onClick={() => {
                            setScheduleApplicationId(evc.application_id);
                            setShowScheduleModal(true);
                          }}
                          className="btn-primary text-xs py-1 px-2.5 inline-flex items-center gap-1"
                        >
                          <CalendarPlus className="w-3 h-3" />
                          Schedule
                        </button>
                      )}
                      {(user.role === 'REGIONAL_OFFICER' || user.role === 'SYSTEM_ADMIN') && evc.status === 'SCHEDULED' && (
                        <button
                          onClick={() => {
                            setSelectedEvcId(evc.id);
                            setShowFindingsModal(true);
                          }}
                          className="btn-primary text-xs py-1 px-2.5"
                        >
                          Submit Findings
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

      {/* Modal: Schedule EVC inspection */}
      <Modal isOpen={showScheduleModal} onClose={() => setShowScheduleModal(false)} title="Schedule EVC Inspection">
        <form onSubmit={handleScheduleInspection} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Inspection date and time *</label>
            <input
              type="datetime-local"
              required
              value={scheduledDate}
              onChange={e => setScheduledDate(e.target.value)}
              min={new Date().toISOString().slice(0, 16)}
              className="w-full text-xs border border-slate-300 rounded p-2"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Inspection mode *</label>
            <select value={inspectionMode} onChange={e => setInspectionMode(e.target.value)} className="w-full text-xs border border-slate-300 rounded p-2 bg-white">
              <option value="PHYSICAL_VISIT">Physical visit</option>
              <option value="HYBRID">Hybrid</option>
              <option value="VIRTUAL">Virtual</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Venue / meeting details</label>
            <input value={inspectionVenue} onChange={e => setInspectionVenue(e.target.value)} placeholder="Institution campus or meeting details" className="w-full text-xs border border-slate-300 rounded p-2" />
          </div>
          <div className="pt-3 border-t flex justify-end gap-2">
            <button type="button" onClick={() => setShowScheduleModal(false)} className="btn-secondary text-xs">Cancel</button>
            <button type="submit" disabled={actionLoading} className="btn-primary text-xs">{actionLoading ? 'Scheduling...' : 'Confirm schedule'}</button>
          </div>
        </form>
      </Modal>

      {/* Modal: Submit Findings */}
      <Modal isOpen={showFindingsModal} onClose={() => setShowFindingsModal(false)} title="Record EVC Committee Findings">
        <form onSubmit={handleCompleteFindings} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Committee Recommendation</label>
            <select
              value={outcome}
              onChange={e => setOutcome(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded p-2 bg-white"
            >
              <option value="RECOMMENDED">Recommended for Next Stage</option>
              <option value="DEFICIENT">Deficiencies Observed on Ground</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Findings & Observations Summary *</label>
            <textarea
              required
              rows={4}
              value={findingsSummary}
              onChange={e => setFindingsSummary(e.target.value)}
              placeholder="Record physical infrastructure observations, library titles verification, laboratory equipment status..."
              className="w-full text-xs border border-slate-300 rounded p-2.5"
            />
          </div>

          <div className="pt-3 border-t flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowFindingsModal(false)}
              className="btn-secondary text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={actionLoading}
              className="btn-primary text-xs"
            >
              {actionLoading ? 'Saving...' : 'Finalize Report'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
