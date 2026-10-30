import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ApplicationEvent, User } from '../types';
import { History, Search, ShieldCheck } from 'lucide-react';

interface AuditPageProps {
  user: User;
  onOpenCase: (id: string) => void;
}

export const AuditPage: React.FC<AuditPageProps> = ({ user, onOpenCase }) => {
  const [events, setEvents] = useState<ApplicationEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState('');

  const loadAuditEvents = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      // Load recent applications to compile journal
      const apps = await api.listApplications({ pageSize: 20 });
      const allEvents: ApplicationEvent[] = [];
      for (const app of apps.items.slice(0, 5)) {
        const history = await api.getApplicationHistory(app.id);
        allEvents.push(...history);
      }
      allEvents.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setEvents(allEvents);
    } catch (err: any) {
      console.error('Failed to load audit events:', err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditEvents();
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void loadAuditEvents(false);
    }, 8000);
    return () => window.clearInterval(timer);
  }, []);

  const filtered = filterAction
    ? events.filter(e => e.action === filterAction)
    : events;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <History className="w-5 h-5 text-blue-700" />
            <span>Tamper-Evident System Audit Trail</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Hash-chained event snapshots with actor accountability; use the admin verification control to check integrity
          </p>
        </div>

        <select
          value={filterAction}
          onChange={e => setFilterAction(e.target.value)}
          className="text-xs border border-slate-300 rounded-md py-2 px-3 bg-white text-slate-700"
        >
          <option value="">All Action Types</option>
          <option value="SUBMIT">Submissions</option>
          <option value="ADVANCE">Stage Advances</option>
          <option value="RETURN_DEFICIENCY">Deficiency Notices</option>
          <option value="RESUBMIT">Resubmissions</option>
          <option value="VERIFY_UNDERTAKING">Compliance Verifications</option>
          <option value="UPLOAD_DOCUMENT">Document Uploads</option>
        </select>
      </div>

      <div className="portal-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="portal-table">
            <thead>
              <tr>
                <th>Timestamp (IST)</th>
                <th>Action</th>
                <th>Transition</th>
                <th>Actor & Assigned Role</th>
                <th>Official Reason / Justification</th>
                <th>Case Link</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-slate-400">
                    Compiling chronological audit stream...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-xs text-slate-400">
                    No audit records found matching criteria.
                  </td>
                </tr>
              ) : (
                filtered.map(ev => (
                  <tr key={ev.id}>
                    <td className="text-xs font-mono text-slate-600">
                      {new Date(ev.created_at).toLocaleString('en-IN')}
                    </td>
                    <td>
                      <span className="font-mono text-xs font-bold text-blue-900 bg-blue-100 px-2 py-0.5 rounded">
                        {ev.action}
                      </span>
                    </td>
                    <td className="text-xs text-slate-700">
                      {ev.from_stage && ev.to_stage ? (
                        <span>
                          {ev.from_stage} → {ev.to_stage}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    <td className="text-xs">
                      <div className="font-semibold text-slate-800">{ev.actor_name || ev.actor_role}</div>
                      <div className="text-[10px] text-slate-500 font-mono">Role: {ev.actor_role}</div>
                    </td>
                    <td className="text-xs text-slate-700 max-w-sm">
                      {ev.reason ? (
                        <span className="italic">"{ev.reason}"</span>
                      ) : (
                        <span className="text-slate-400 italic">No remarks recorded</span>
                      )}
                    </td>
                    <td>
                      <button
                        onClick={() => onOpenCase(ev.application_id)}
                        className="btn-secondary text-xs py-1 px-2.5"
                      >
                        Open Case
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
