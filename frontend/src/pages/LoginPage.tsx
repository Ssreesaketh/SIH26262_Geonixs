import React, { useState } from 'react';
import { api } from '../services/api';
import { ShieldCheck, ArrowRight, UserCheck, AlertCircle, LockKeyhole, FileCheck2, Clock3, Activity } from 'lucide-react';
import { User } from '../types';

interface LoginPageProps {
  onLoginSuccess: (user: User) => void;
}

const DEMO_PASSWORD = 'Admin@AICTE2026!';

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('officer.north@aicte.gov.in');
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const demoAccounts = [
    {
      role: 'Regional officer',
      email: 'officer.north@aicte.gov.in',
      desc: 'Scrutiny, returns and regional workload',
      initials: 'RO'
    },
    {
      role: 'Institution user',
      email: 'principal@zenith.edu.in',
      desc: 'Applications, evidence and renewals',
      initials: 'IN'
    },
    {
      role: 'Bureau officer',
      email: 'bureau.hq@aicte.gov.in',
      desc: 'Cross-region oversight and escalations',
      initials: 'BO'
    },
    {
      role: 'System administrator',
      email: 'admin@aicte.gov.in',
      desc: 'Workflow settings and demo operations',
      initials: 'SA'
    }
  ];

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.login(email, password);
      onLoginSuccess(res.user);
    } catch (err: any) {
      setError(err.message || 'Unable to sign in. Check the selected demo account and password.');
    } finally {
      setLoading(false);
    }
  };

  const selectDemoAccount = (accEmail: string) => {
    setEmail(accEmail);
    setPassword(DEMO_PASSWORD);
    setError(null);
  };

  return (
    <main className="login-screen">
      <div className="login-layout">
        <section className="login-story" aria-label="Platform overview">
          <div className="login-brand">
            <div className="login-brand-mark" aria-hidden="true"><ShieldCheck size={25} strokeWidth={1.8} /></div>
            <div className="login-brand-copy">
              <span className="login-brand-name">SIH26262</span>
              <span className="login-brand-label">PRODUCT PROTOTYPE</span>
            </div>
          </div>

          <div className="login-story-content">
            <div className="login-eyebrow"><span /> APPROVAL OPERATIONS</div>
            <h1>Every case.<br />Every obligation.<br /><em>Clearly accounted for.</em></h1>
            <p className="login-story-intro">
              A unified workspace concept for approval workflows, institutional compliance and time-sensitive administrative action.
            </p>

            <div className="login-feature-list">
              <div className="login-feature">
                <span className="login-feature-icon"><Activity size={17} /></span>
                <div><strong>Operational visibility</strong><small>Track pendency, workload and progress.</small></div>
              </div>
              <div className="login-feature">
                <span className="login-feature-icon"><Clock3 size={17} /></span>
                <div><strong>Deadline awareness</strong><small>Surface upcoming and overdue obligations.</small></div>
              </div>
              <div className="login-feature">
                <span className="login-feature-icon"><FileCheck2 size={17} /></span>
                <div><strong>Traceable actions</strong><small>Keep decisions, submissions and history connected.</small></div>
              </div>
            </div>
          </div>

          <div className="login-story-footer">
            <span className="prototype-dot" />
            <span>Independent hackathon prototype</span>
            <span className="login-footer-divider">·</span>
            <span>Synthetic data only</span>
          </div>
        </section>

        <section className="login-panel" aria-label="Sign in">
          <div className="login-panel-head">
            <div className="login-panel-kicker">DEMO WORKSPACE</div>
            <h2>Sign in to continue</h2>
            <p>Choose a persona to explore the workflows and responsibilities available in this prototype.</p>
          </div>

          {error && (
            <div className="login-error" role="alert">
              <AlertCircle size={19} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="login-persona-label">SELECT A DEMO ROLE</div>
          <div className="login-personas">
            {demoAccounts.map(acc => {
              const selected = email === acc.email;
              return (
                <button
                  type="button"
                  key={acc.email}
                  onClick={() => selectDemoAccount(acc.email)}
                  className={`login-persona${selected ? ' is-selected' : ''}`}
                  aria-pressed={selected}
                >
                  <span className="login-persona-avatar">{acc.initials}</span>
                  <span className="login-persona-copy">
                    <strong>{acc.role}</strong>
                    <small>{acc.desc}</small>
                  </span>
                  <span className="login-persona-check"><UserCheck size={16} /></span>
                </button>
              );
            })}
          </div>

          <form onSubmit={handleLogin} className="login-form">
            <div className="login-field">
              <label htmlFor="login-email">Email address</label>
              <input
                id="login-email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="login-input"
              />
            </div>
            <div className="login-field">
              <label htmlFor="login-password">Demo password</label>
              <input
                id="login-password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="login-input"
              />
            </div>

            <button type="submit" disabled={loading} className="login-submit">
              <span>{loading ? 'Signing in…' : 'Open workspace'}</span>
              {loading ? <span className="login-submit-spinner" /> : <ArrowRight size={18} />}
            </button>
          </form>

          <div className="login-security-note">
            <LockKeyhole size={15} />
            <span>Local demo accounts are for synthetic data only. Do not use real institutional records.</span>
          </div>
          <div className="login-disclaimer">Not an official AICTE service or production deployment.</div>
        </section>
      </div>
    </main>
  );
};
