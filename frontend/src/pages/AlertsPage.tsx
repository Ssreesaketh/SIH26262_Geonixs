import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { NotificationItem, User } from '../types';
import { AlertTriangle, CheckCheck, RefreshCw, Clock, ArrowRight, ShieldAlert } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';

interface AlertsPageProps {
  user: User;
  onOpenCase: (id: string) => void;
}

export const AlertsPage: React.FC<AlertsPageProps> = ({ user, onOpenCase }) => {
  const [alerts, setAlerts] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [sweepLoading, setSweepLoading] = useState(false);
  const [sweepMsg, setSweepMsg] = useState<string | null>(null);

  const loadAlerts = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const data = await api.listAlerts(severityFilter || undefined, statusFilter || undefined);
      setAlerts(data);
    } catch (err: any) {
      console.error('Failed to load alerts:', err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void loadAlerts(false);
    }, 8000);
    return () => window.clearInterval(timer);
  }, [severityFilter, statusFilter]);

  const handleSweep = async () => {
    setSweepLoading(true);
    setSweepMsg(null);
    try {
      const res = await api.checkDeadlines();
      setSweepMsg(
        `Sweep completed at ${new Date(res.checked_at).toLocaleTimeString()}: Evaluated ${res.total_evaluated} obligations, ${res.new_alerts_created} new alerts created.`
      );
      await loadAlerts();
    } catch (err: any) {
      setSweepMsg(`Sweep failed: ${err.message}`);
    } finally {
      setSweepLoading(false);
    }
  };

  const handleAcknowledge = async (id: string) => {
    try {
      await api.acknowledgeAlert(id);
      await loadAlerts();
    } catch (err: any) {
      alert(err.message || 'Failed to acknowledge alert');
    }
  };

  const handleResolve = async (id: string) => {
    try {
      await api.resolveAlert(id);
      await loadAlerts();
    } catch (err: any) {
      alert(err.message || 'Failed to resolve alert');
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-600" />
            <span>Alerts & escalations</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Deadlines, EVC delays, document expiry and compliance reminders.
          </p>
        </div>

        <button
          onClick={handleSweep}
          disabled={sweepLoading}
          className="btn-primary text-xs"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${sweepLoading ? 'animate-spin' : ''}`} />
          <span>{sweepLoading ? 'Checking deadlines...' : 'Check deadlines'}</span>
        </button>
      </div>

      {sweepMsg && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-900 flex items-center justify-between">
          <span>{sweepMsg}</span>
          <button onClick={() => setSweepMsg(null)} className="font-bold text-blue-700 ml-4">
            ×
          </button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="portal-card p-4 flex flex-wrap gap-4 items-center justify-between">
        <div className="flex items-center gap-3">
          <select
            value={severityFilter}
            onChange={e => setSeverityFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-md py-2 px-3 bg-white text-slate-700"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical (Breached SLAs)</option>
            <option value="WARNING">Warning (Within 48h / Expiring)</option>
            <option value="INFO">Informational</option>
          </select>

          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-md py-2 px-3 bg-white text-slate-700"
          >
            <option value="">All Statuses</option>
            <option value="UNREAD">Unread / Active</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>

        <div className="text-xs text-slate-500">
          Showing {alerts.length} notifications
        </div>
      </div>

      {/* Alerts Stream */}
      <div className="space-y-3">
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400">Loading alerts stream...</div>
        ) : alerts.length === 0 ? (
          <div className="portal-card p-12 text-center text-slate-500 text-xs">
            <CheckCheck className="w-8 h-8 text-emerald-600 mx-auto mb-2 opacity-80" />
            <div className="font-semibold text-slate-800 text-sm">No Outstanding Escalations</div>
            <div className="text-slate-400 mt-1">All application stages, undertakings, and leases are operating within prescribed windows.</div>
          </div>
        ) : (
          alerts.map(alt => {
            const isCritical = alt.severity === 'CRITICAL';
            return (
              <div
                key={alt.id}
                className={`portal-card p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition-all ${
                  isCritical ? 'border-l-4 border-l-red-600 bg-red-50/20' : 'border-l-4 border-l-amber-500'
                }`}
              >
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusBadge status={alt.severity} />
                    <span className="font-bold text-xs text-slate-900">
                      {alt.application_no ? `Case ${alt.application_no}` : alt.notification_type}
                    </span>
                    <span className="text-[10px] bg-slate-100 text-slate-700 border border-slate-200 px-1.5 py-0.2 rounded font-mono font-semibold">
                      Escalation Level {alt.escalation_level}
                    </span>
                    <span className="text-[10px] text-slate-500 font-mono">
                      Target Role: {alt.recipient_role}
                    </span>
                  </div>

                  <div className="text-xs text-slate-800 leading-relaxed font-medium">
                    {alt.message}
                  </div>

                  <div className="text-[11px] text-slate-400 font-mono flex items-center gap-3">
                    <span>Generated: {new Date(alt.created_at).toLocaleString('en-IN')}</span>
                    {alt.due_at && (
                      <span>• Target Due: {new Date(alt.due_at).toLocaleDateString('en-IN')}</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {alt.status === 'UNREAD' && (
                    <button
                      onClick={() => handleAcknowledge(alt.id)}
                      className="btn-secondary text-xs py-1 px-2.5"
                    >
                      Acknowledge
                    </button>
                  )}

                  {alt.status !== 'RESOLVED' && (
                    <button
                      onClick={() => handleResolve(alt.id)}
                      className="btn-primary text-xs py-1 px-2.5 bg-emerald-700 hover:bg-emerald-800"
                    >
                      Resolve
                    </button>
                  )}

                  {alt.application_id && (
                    <button
                      onClick={() => onOpenCase(alt.application_id!)}
                      className="btn-secondary text-xs py-1 px-2.5 flex items-center gap-1"
                    >
                      <span>Open Case</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
