import React, { useEffect, useState } from 'react';
import { BookOpenCheck, Bot, FileUp, LoaderCircle, Search, ShieldAlert, ExternalLink } from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';

interface Props { user: User }

export const AIReviewPage: React.FC<Props> = ({ user }) => {
  const [question, setQuestion] = useState('What requirements should an officer verify for this document type?');
  const [answer, setAnswer] = useState<any>(null);
  const [asking, setAsking] = useState(false);
  const [sources, setSources] = useState<any[]>([]);
  const [sourceTitle, setSourceTitle] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [sourceVersion, setSourceVersion] = useState('');
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');

  const loadSources = async () => {
    try { setSources(await api.listRegulatorySources()); } catch (e: any) { setError(e.message || 'Could not load the source catalogue.'); }
  };
  useEffect(() => { void loadSources(); }, []);

  const ask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (question.trim().length < 3) return;
    setAsking(true); setError(''); setNotice('');
    try { setAnswer(await api.askRegulatoryQuestion(question.trim())); }
    catch (e: any) { setError(e.message || 'Question could not be processed.'); }
    finally { setAsking(false); }
  };

  const uploadSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceFile || !sourceTitle.trim()) { setError('Choose a PDF and provide its source title.'); return; }
    if (sourceFile.size > 10 * 1024 * 1024) { setError('The source PDF must be 10 MB or smaller.'); return; }
    setUploading(true); setError(''); setNotice('');
    try {
      const fd = new FormData(); fd.append('file', sourceFile); fd.append('source_title', sourceTitle.trim());
      if (sourceUrl.trim()) fd.append('source_url', sourceUrl.trim());
      if (sourceVersion.trim()) fd.append('source_version', sourceVersion.trim());
      const result = await api.uploadRegulatorySource(fd);
      setNotice(`Indexed ${result.chunks_added} text chunks across ${result.page_count} pages.`);
      setSourceFile(null); setSourceTitle(''); setSourceUrl(''); setSourceVersion('');
      const input = document.getElementById('regulatory-source-file') as HTMLInputElement | null;
      if (input) input.value = '';
      await loadSources();
    } catch (e: any) { setError(e.message || 'Source indexing failed.'); }
    finally { setUploading(false); }
  };

  return <div className="p-6 space-y-6 max-w-7xl mx-auto">
    <header className="pb-4 border-b border-slate-200">
      <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2"><Bot className="w-5 h-5 text-blue-700"/> Regulatory AI Assistant</h1>
      <p className="text-xs text-slate-500 mt-1">Source-grounded guidance from administrator-indexed regulatory documents. This assistant cannot make official decisions.</p>
    </header>
    <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 flex gap-3 text-amber-900">
      <ShieldAlert className="w-5 h-5 shrink-0 mt-0.5"/>
      <div className="text-xs"><strong>Advisory only.</strong> Confirm the applicable regulation and effective version before relying on any answer. Uploaded institution documents are not automatically added to the shared knowledge base.</div>
    </div>
    {error && <div role="alert" className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    {notice && <div role="status" className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</div>}
    <section className="portal-card p-5 space-y-4">
      <div className="flex items-center gap-2"><Search className="w-4 h-4 text-blue-700"/><h2 className="text-sm font-bold text-slate-900">Ask about a regulation or requirement</h2></div>
      <form onSubmit={ask} className="space-y-3">
        <textarea value={question} onChange={e => setQuestion(e.target.value)} rows={3} maxLength={2000} className="w-full border border-slate-300 rounded-md p-3 text-sm" placeholder="Ask a question about an indexed official source..." />
        <button className="btn-primary text-xs" type="submit" disabled={asking}>{asking ? <LoaderCircle className="w-4 h-4 animate-spin"/> : <Search className="w-4 h-4"/>}{asking ? 'Searching sources…' : 'Search approved sources'}</button>
      </form>
      {answer && <div className="rounded-lg border border-slate-200 bg-slate-50 p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2"><h3 className="text-sm font-bold text-slate-900">Response</h3><span className="text-[10px] uppercase tracking-wide rounded-full bg-white border border-slate-200 px-2 py-1 text-slate-600">{String(answer.engine_mode || 'retrieval').replace(/_/g, ' ')}</span></div>
        <p className="text-sm text-slate-800 whitespace-pre-wrap leading-6">{answer.answer}</p>
        {answer.sources?.length > 0 && <div className="border-t border-slate-200 pt-3"><h4 className="text-xs font-bold text-slate-700 mb-2">Retrieved sources</h4><ul className="space-y-2">{answer.sources.map((s: any, i: number) => <li key={`${s.title}-${s.page}-${i}`} className="text-xs text-slate-600"><strong>{s.title}</strong>{s.page ? ` · page ${s.page}` : ''}{s.version ? ` · version ${s.version}` : ''}{s.url && <a className="ml-2 inline-flex items-center gap-1 text-blue-700 underline" href={s.url} target="_blank" rel="noreferrer">Source <ExternalLink className="w-3 h-3"/></a>}</li>)}</ul></div>}
        <p className="text-[11px] text-slate-500">{answer.disclaimer}</p>
      </div>}
    </section>
    {user.role === 'SYSTEM_ADMIN' && <section className="portal-card p-5 space-y-4">
      <div className="flex items-center gap-2"><FileUp className="w-4 h-4 text-blue-700"/><h2 className="text-sm font-bold text-slate-900">Curate official knowledge sources</h2></div>
      <p className="text-xs text-slate-500">Only upload verified, authorized source documents. PDF text is extracted into page-aware chunks; source URL/version metadata should be recorded to support review.</p>
      <form onSubmit={uploadSource} className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <label className="text-xs text-slate-700">Source title *<input required value={sourceTitle} onChange={e => setSourceTitle(e.target.value)} maxLength={255} className="mt-1 w-full border border-slate-300 rounded-md p-2" placeholder="AICTE Approval Process Handbook"/></label>
        <label className="text-xs text-slate-700">Version / effective period<input value={sourceVersion} onChange={e => setSourceVersion(e.target.value)} maxLength={100} className="mt-1 w-full border border-slate-300 rounded-md p-2" placeholder="e.g. 2026–27; verify official dates"/></label>
        <label className="text-xs text-slate-700 md:col-span-2">Official source URL<input value={sourceUrl} onChange={e => setSourceUrl(e.target.value)} maxLength={1000} type="url" className="mt-1 w-full border border-slate-300 rounded-md p-2" placeholder="https://..."/></label>
        <label className="text-xs text-slate-700 md:col-span-2">PDF file (maximum 10 MB) *<input id="regulatory-source-file" required type="file" accept="application/pdf,.pdf" onChange={e => setSourceFile(e.target.files?.[0] || null)} className="mt-1 block w-full text-xs"/></label>
        <div className="md:col-span-2"><button disabled={uploading} className="btn-primary text-xs" type="submit">{uploading ? <LoaderCircle className="w-4 h-4 animate-spin"/> : <FileUp className="w-4 h-4"/>}{uploading ? 'Indexing source…' : 'Index regulatory PDF'}</button></div>
      </form>
    </section>}
    <section className="portal-card p-5 space-y-3">
      <div className="flex items-center gap-2"><BookOpenCheck className="w-4 h-4 text-blue-700"/><h2 className="text-sm font-bold text-slate-900">Indexed regulatory source catalogue</h2></div>
      {sources.length === 0 ? <p className="text-xs text-slate-500">No regulatory sources have been indexed yet. A system administrator must upload a verified official PDF.</p> : <div className="overflow-x-auto"><table className="portal-table"><thead><tr><th>Source</th><th>Version</th><th>Pages indexed</th><th>Chunks</th>{user.role === 'SYSTEM_ADMIN' && <th>Action</th>}</tr></thead><tbody>{sources.map((s, i) => <tr key={`${s.content_sha256}-${i}`}><td><div className="text-xs font-semibold text-slate-800">{s.source_title}</div>{s.source_url && <a href={s.source_url} target="_blank" rel="noreferrer" className="text-[10px] text-blue-700 underline">Open source</a>}</td><td className="text-xs">{s.source_version || 'Not recorded'}</td><td className="text-xs">{s.pages}</td><td className="text-xs">{s.chunks}</td>{user.role === 'SYSTEM_ADMIN' && <td><button type="button" className="btn-secondary text-xs" onClick={async () => { if (!window.confirm(`Deactivate ${s.source_title}? Existing evaluations remain saved; this source will no longer be retrieved.`)) return; try { await api.deactivateRegulatorySource(s.content_sha256); setNotice(`Deactivated ${s.source_title}.`); await loadSources(); } catch (e: any) { setError(e.message || 'Deactivation failed'); } }}>Deactivate</button></td>}</tr>)}</tbody></table></div>}
    </section>
  </div>;
};
