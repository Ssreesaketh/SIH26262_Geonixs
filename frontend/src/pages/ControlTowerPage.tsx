import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  DashboardSummary,
  StagePendency,
  RegionalWorkload,
  NotificationItem,
  User,
  Application,
  EVCEvent,
  DocumentItem
} from '../types';
import {
  Activity,
  AlertTriangle,
  Clock,
  FileCheck2,
  Calendar,
  ShieldAlert,
  RefreshCw,
  ArrowRight,
  TrendingUp,
  MapPin
} from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';

interface ControlTowerPageProps {
  user: User;
  onNavigateApplications: (stage?: string) => void;
  onNavigateAlerts: () => void;
  onSelectApplication: (id: string) => void;
}

export const ControlTowerPage: React.FC<ControlTowerPageProps> = ({
  user,
  onNavigateApplications,
  onNavigateAlerts,
  onSelectApplication
}) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [pendency, setPendency] = useState<StagePendency[]>([]);
  const [regions, setRegions] = useState<RegionalWorkload[]>([]);
  const [alerts, setAlerts] = useState<NotificationItem[]>([]);
  const [institutionApplications, setInstitutionApplications] = useState<Application[]>([]);
  const [institutionInspections, setInstitutionInspections] = useState<EVCEvent[]>([]);
  const [institutionDocuments, setInstitutionDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sweepLoading, setSweepLoading] = useState(false);
  const [sweepResult, setSweepResult] = useState<string | null>(null);

  const loadData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      if (user.role === 'INSTITUTION_USER') {
        const [sum, apps, inspections, docs] = await Promise.all([
          api.getDashboardSummary(),
          api.listApplications({ pageSize: 100 }),
          api.listEvc(),
          api.listDocuments()
        ]);
        setSummary(sum);
        setInstitutionApplications(apps.items);
        setInstitutionInspections(inspections);
        setInstitutionDocuments(docs);
        setPendency([]);
        setRegions([]);
        setAlerts([]);
      } else {
        const [sum, pend, reg, alt] = await Promise.all([
          api.getDashboardSummary(),
          api.getStagePendency(),
          api.getRegionalWorkload(),
          api.listAlerts(undefined, 'UNREAD')
        ]);
        setSummary(sum);
        setPendency(pend);
        setRegions(reg);
        setAlerts(alt.slice(0, 5)); // Top 5 urgent alerts
      }
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Keep separate role sessions in sync with changes committed by other users.
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void loadData(false);
    }, 5000);
    return () => window.clearInterval(timer);
  }, []);

  const handleRunSweep = async () => {
    setSweepLoading(true);
    setSweepResult(null);
    try {
      const res = await api.checkDeadlines();
      setSweepResult(
        `Sweep completed: Evaluated ${res.total_evaluated} obligations. ${res.new_alerts_created} new alerts registered.`
      );
      await loadData();
    } catch (err: any) {
      setSweepResult(`Sweep failed: ${err.message}`);
    } finally {
      setSweepLoading(false);
    }
  };

  if (loading && !summary) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <div className="flex items-center gap-3 text-slate-500 text-sm">
          <RefreshCw className="w-5 h-5 animate-spin text-blue-600" />
          <span>Loading overview metrics...</span>
        </div>
      </div>
    );
  }

  if (user.role === 'INSTITUTION_USER') {
    const institutionName = institutionApplications[0]?.institution_name || 'Your institution';
    return (
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        <div className="pb-4 border-b border-slate-200">
          <h1 className="text-xl font-bold text-slate-900">My institution overview</h1>
          <p className="text-sm text-slate-600 mt-1">{institutionName}</p>
          <p className="text-xs text-slate-500 mt-1">Private workspace for your applications, documents and inspection schedule.</p>
          <p className="text-[11px] text-emerald-700 mt-2">Live sync enabled · refreshes every 5 seconds</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="portal-card p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase">My applications</div>
            <div className="text-2xl font-bold text-slate-900 mt-1">{institutionApplications.length}</div>
          </div>
          <div className="portal-card p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase">Active applications</div>
            <div className="text-2xl font-bold text-slate-900 mt-1">{summary?.total_active || 0}</div>
          </div>
          <div className="portal-card p-4">
            <div className="text-xs font-semibold text-slate-500 uppercase">My documents</div>
            <div className="text-2xl font-bold text-slate-900 mt-1">{institutionDocuments.length}</div>
          </div>
        </div>

        <section className="portal-card p-5 space-y-3">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-sm font-bold text-slate-900">My applications and current stage</h2>
            <button onClick={() => onNavigateApplications()} className="btn-secondary text-xs">View all</button>
          </div>
          {institutionApplications.length === 0 ? (
            <p className="text-sm text-slate-500 py-5 text-center">No applications are linked to this institution yet.</p>
          ) : institutionApplications.map(app => {
            const inspections = institutionInspections.filter(item => item.application_id === app.id);
            return (
              <button key={app.id} type="button" onClick={() => onSelectApplication(app.id)} className="w-full text-left border border-slate-200 rounded-lg p-4 hover:border-blue-400 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <div className="font-mono text-xs font-bold text-blue-800">{app.application_no}</div>
                    <div className="text-sm font-semibold text-slate-900 mt-1">{app.application_type.replace(/_/g, ' ')}</div>
                  </div>
                  <div className="flex gap-2 flex-wrap">
                    <StatusBadge status={app.current_stage_code} />
                    <StatusBadge status={app.workflow_status} />
                  </div>
                </div>
                <div className="mt-3 text-xs text-slate-600">
                  {inspections.length === 0 ? 'Inspection: Not scheduled' : inspections.map(item => `Inspection: ${item.scheduled_date ? new Date(item.scheduled_date).toLocaleString('en-IN') : 'Awaiting schedule'} · ${item.status.replace(/_/g, ' ')}`).join(' | ')}
                </div>
                {app.workflow_status === 'DEFICIENCY_RETURNED' && <div className="mt-2 text-xs font-semibold text-amber-700">Action required: review the deficiency notice and resubmit.</div>}
              </button>
            );
          })}
        </section>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            <span>Operations overview</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            A consolidated view of application progress, upcoming deadlines and compliance obligations.
          </p>
          <p className="text-[11px] text-emerald-700 mt-2 inline-flex items-center gap-1.5"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> Live sync enabled · refreshes every 5 seconds</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleRunSweep}
            disabled={sweepLoading}
            className="btn-primary text-xs cursor-pointer shadow-xs"
            title="Idempotently inspect all stage deadlines, undertakings, and lease expiries"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${sweepLoading ? 'animate-spin' : ''}`} />
            <span>{sweepLoading ? 'Checking deadlines...' : 'Check deadlines'}</span>
          </button>
        </div>
      </div>

      {sweepResult && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-xs text-blue-800 flex items-center justify-between animate-in fade-in">
          <span>{sweepResult}</span>
          <button onClick={() => setSweepResult(null)} className="text-blue-500 hover:text-blue-700 font-bold ml-4">
            ×
          </button>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-6 gap-4">
        {/* Total Active */}
        <div
          onClick={() => onNavigateApplications()}
          className="portal-card p-4 hover:border-blue-400 transition-all cursor-pointer group"
        >
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Cases</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{summary?.total_active || 0}</div>
          <div className="text-[11px] text-blue-600 font-medium mt-1 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform">
            <span>View All</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </div>

        {/* Overdue Stages */}
        <div
          onClick={() => onNavigateAlerts()}
          className="portal-card p-4 border-l-4 border-l-red-600 hover:border-red-400 transition-all cursor-pointer group"
        >
          <div className="text-xs font-semibold text-red-700 uppercase tracking-wider flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
            <span>Overdue stages</span>
          </div>
          <div className="text-2xl font-bold text-red-600 mt-1">{summary?.overdue_stages || 0}</div>
          <div className="text-[11px] text-red-700 font-medium mt-1">Requires Immediate Action</div>
        </div>

        {/* Upcoming SLA (48h) */}
        <div className="portal-card p-4 border-l-4 border-l-amber-500">
          <div className="text-xs font-semibold text-amber-700 uppercase tracking-wider flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-amber-600" />
            <span>Due soon</span>
          </div>
          <div className="text-2xl font-bold text-amber-600 mt-1">{summary?.upcoming_sla || 0}</div>
          <div className="text-[11px] text-slate-500 mt-1">Due within the configured warning window</div>
        </div>

        {/* Expired / Critical Documents */}
        <div className="portal-card p-4 border-l-4 border-l-rose-500">
          <div className="text-xs font-semibold text-rose-700 uppercase tracking-wider flex items-center gap-1">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
            <span>Expired Leases</span>
          </div>
          <div className="text-2xl font-bold text-rose-600 mt-1">{summary?.expired_documents || 0}</div>
          <div className="text-[11px] text-slate-500 mt-1">Lease Deeds & NOCs</div>
        </div>

        {/* Pending EVC */}
        <div className="portal-card p-4 border-l-4 border-l-indigo-500">
          <div className="text-xs font-semibold text-indigo-700 uppercase tracking-wider flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-indigo-600" />
            <span>Pending EVC</span>
          </div>
          <div className="text-2xl font-bold text-indigo-600 mt-1">{summary?.pending_evc || 0}</div>
          <div className="text-[11px] text-slate-500 mt-1">Awaiting Inspection</div>
        </div>

        {/* Pending Undertakings */}
        <div className="portal-card p-4 border-l-4 border-l-emerald-600">
          <div className="text-xs font-semibold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
            <FileCheck2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Undertakings due</span>
          </div>
          <div className="text-2xl font-bold text-emerald-700 mt-1">{summary?.pending_undertakings || 0}</div>
          <div className="text-[11px] text-slate-500 mt-1">Conditional Filings</div>
        </div>
      </div>

      {/* Middle Section: Stage Pendency & Regional Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Stage Pendency */}
        <div className="portal-card p-5">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-blue-600" />
            <span>Applications by stage</span>
          </h2>
          <div className="space-y-3">
            {pendency.length === 0 ? (
              <div className="text-xs text-slate-400 py-4 text-center">No active applications in stages</div>
            ) : (
              pendency.map(item => {
                const max = Math.max(...pendency.map(p => p.count), 1);
                const pct = Math.round((item.count / max) * 100);
                return (
                  <div
                    key={item.stage_code}
                    onClick={() => onNavigateApplications(item.stage_code)}
                    className="p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 cursor-pointer transition-colors"
                  >
                    <div className="flex justify-between text-xs font-medium text-slate-700 mb-1.5">
                      <span>{item.stage_name}</span>
                      <span className="font-bold text-slate-900">{item.count} cases</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${pct}%` }}
                      ></div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Regional Workload */}
        <div className="portal-card p-5">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2 mb-4">
            <MapPin className="w-4 h-4 text-blue-600" />
            <span>Regional workload</span>
          </h2>
          <div className="overflow-x-auto">
            <table className="portal-table">
              <thead>
                <tr>
                  <th>Regional Office</th>
                  <th>Active Cases</th>
                  <th>Overdue Cases</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {regions.map(r => (
                  <tr key={r.region_id}>
                    <td className="font-semibold text-slate-800">{r.region_name}</td>
                    <td className="font-mono">{r.active_count}</td>
                    <td className="font-mono text-red-600 font-bold">{r.overdue_count}</td>
                    <td>
                      {r.overdue_count > 0 ? (
                        <span className="badge badge-critical">Attention</span>
                      ) : (
                        <span className="badge badge-success">On Track</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Priority Escalation Queue */}
      <div className="portal-card p-5 border-t-4 border-t-red-600">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span>Overdue and urgent actions</span>
          </h2>
          <button
            onClick={onNavigateAlerts}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 cursor-pointer"
          >
            <span>View all alerts</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {alerts.length === 0 ? (
          <div className="text-xs text-slate-400 py-6 text-center bg-slate-50 rounded-lg border border-dashed border-slate-200">
            No unacknowledged priority alerts are currently in this queue.
          </div>
        ) : (
          <div className="space-y-2.5">
            {alerts.map(alt => (
              <div
                key={alt.id}
                className="p-3.5 rounded-lg border border-red-200 bg-red-50/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={alt.severity} />
                    <span className="text-xs font-bold text-slate-800">
                      {alt.application_no ? `Application ${alt.application_no}` : alt.notification_type}
                    </span>
                    <span className="text-[10px] bg-red-100 text-red-800 font-bold px-1.5 py-0.5 rounded">
                      Level {alt.escalation_level}
                    </span>
                  </div>
                  <div className="text-xs text-slate-700">{alt.message}</div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {alt.application_id && (
                    <button
                      onClick={() => onSelectApplication(alt.application_id!)}
                      className="btn-secondary text-xs py-1.5 px-3"
                    >
                      Open Case
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
