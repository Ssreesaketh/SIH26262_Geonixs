import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { WorkflowTemplate, User } from '../types';
import { Sliders, RotateCcw, Check, Save, ShieldCheck } from 'lucide-react';

interface WorkflowConfigPageProps {
  user: User;
}

export const WorkflowConfigPage: React.FC<WorkflowConfigPageProps> = ({ user }) => {
  const [workflows, setWorkflows] = useState<WorkflowTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [resetLoading, setResetLoading] = useState(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [savingId, setSavingId] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await api.listWorkflows();
      setWorkflows(data);
      setDrafts(Object.fromEntries(data.map(wf => [wf.id, JSON.stringify(wf.configuration, null, 2)])));
    } catch (err: any) {
      console.error('Failed to load workflow configurations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSaveRules = async (id: string) => {
    if (user.role !== 'SYSTEM_ADMIN') return;
    setSavingId(id);
    setSaveMessage(null);
    try {
      const parsed = JSON.parse(drafts[id] || '{}');
      const updated = await api.updateWorkflow(id, parsed);
      setSaveMessage(`${updated.code} saved as version ${updated.version}. Existing applications retain their pinned workflow version.`);
      await loadData();
    } catch (err: any) {
      setSaveMessage(`Rules were not saved: ${err.message || 'Check the JSON and rule values.'}`);
    } finally {
      setSavingId(null);
    }
  };

  const handleResetDemo = async () => {
    if (!confirm('Safely reset demonstration dataset back to deterministic initial state?')) return;
    setResetLoading(true);
    setResetMessage(null);
    try {
      const res = await api.resetDemo();
      setResetMessage(res.message);
      await loadData();
    } catch (err: any) {
      setResetMessage(`Reset failed: ${err.message}`);
    } finally {
      setResetLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Sliders className="w-5 h-5 text-blue-700" />
            <span>Workflow configuration</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Configure prototype workflow paths, stage timelines and escalation rules.
          </p>
        </div>

        {user.role === 'SYSTEM_ADMIN' && (
          <button
            onClick={handleResetDemo}
            disabled={resetLoading}
            className="btn-danger text-xs cursor-pointer shadow-xs"
            title="Restore baseline scenarios for evaluation"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${resetLoading ? 'animate-spin' : ''}`} />
            <span>{resetLoading ? 'Resetting demo data...' : 'Reset demo data'}</span>
          </button>
        )}
      </div>

      {saveMessage && (
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800">{saveMessage}</div>
      )}

      {resetMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-900 flex items-center justify-between">
          <span>{resetMessage}</span>
          <button onClick={() => setResetMessage(null)} className="font-bold text-emerald-700 ml-4">
            ×
          </button>
        </div>
      )}

      {/* Workflow Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {workflows.map(wf => (
          <div key={wf.id} className="portal-card p-5 space-y-4 border-t-4 border-t-blue-700">
            <div>
              <div className="flex items-center justify-between">
                <span className="font-mono text-xs font-bold text-blue-900 bg-blue-100 px-2 py-0.5 rounded">
                  {wf.code} (v{wf.version})
                </span>
                <span className="text-[11px] text-emerald-700 font-semibold flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" />
                  <span>Active</span>
                </span>
              </div>
              <h2 className="font-bold text-sm text-slate-900 mt-2">{wf.name}</h2>
            </div>

            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                Ordered Stages Sequence
              </div>
              <div className="flex flex-wrap gap-1.5">
                {wf.configuration.ordered_stages?.map((st: string) => (
                  <span
                    key={st}
                    className="text-[11px] font-mono bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200"
                  >
                    {st}
                  </span>
                ))}
              </div>
            </div>

            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500 mb-1.5">
                Configured Stage SLAs (Days)
              </div>
              <div className="space-y-1 text-xs">
                {Object.entries(wf.configuration.stage_slas || {}).map(([stage, days]) => (
                  <div key={stage} className="flex justify-between py-1 border-b border-slate-100">
                    <span className="text-slate-600 font-mono">{stage}</span>
                    <span className="font-bold text-slate-800">{days} days</span>
                  </div>
                ))}
                {wf.configuration.rectification_sla_days && (
                  <div className="flex justify-between py-1 text-amber-800 font-semibold">
                    <span>Deficiency Rectification Window</span>
                    <span>{wf.configuration.rectification_sla_days} days</span>
                  </div>
                )}
              </div>
            </div>

            {user.role === 'SYSTEM_ADMIN' && (
              <div className="border-t border-slate-200 pt-4 space-y-2">
                <label className="text-[11px] font-bold uppercase tracking-wider text-slate-600">Editable versioned rule JSON</label>
                <textarea
                  value={drafts[wf.id] ?? JSON.stringify(wf.configuration, null, 2)}
                  onChange={e => setDrafts(current => ({ ...current, [wf.id]: e.target.value }))}
                  spellCheck={false}
                  rows={12}
                  className="w-full rounded-md border border-slate-300 bg-slate-950 text-emerald-100 p-3 text-[11px] font-mono"
                  aria-label={`Rule configuration JSON for ${wf.code}`}
                />
                <p className="text-[10px] text-slate-500">Includes stage_slas, warning_threshold_percent (1–99), reminder_windows_hours and escalation_ladder. Values are demo rules, not official AICTE timelines.</p>
                <button onClick={() => handleSaveRules(wf.id)} disabled={savingId === wf.id} className="btn-primary text-xs flex items-center gap-2">
                  <Save className="w-3.5 h-3.5" />{savingId === wf.id ? 'Saving version…' : 'Validate & save new version'}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
      {user.role === 'SYSTEM_ADMIN' && (
        <div className="portal-card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div><div className="text-sm font-bold text-slate-900 flex items-center gap-2"><ShieldCheck className="w-4 h-4 text-blue-700" />Tamper-evident audit chain</div><p className="text-xs text-slate-500 mt-1">Verify the hash chain after the demo actions to detect changed or missing chain entries.</p></div>
          <button onClick={async () => { try { const result = await api.verifyAuditChain(); setSaveMessage(result.valid ? `Audit chain valid — ${result.entries_checked} entries checked.` : `AUDIT CHAIN INVALID at sequence ${result.failed_sequence}: ${result.reason}`); } catch (err: any) { setSaveMessage(`Audit verification failed: ${err.message}`); } }} className="btn-secondary text-xs">Verify audit chain</button>
        </div>
      )}
    </div>
  );
};
