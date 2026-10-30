import React, { useState, useEffect } from 'react';
import { User } from '../types';
import { Bell, LogOut, UserRound, ShieldCheck, Clock3 } from 'lucide-react';

interface NavbarProps {
  user: User;
  onLogout: () => void;
  onNavigateAlerts: () => void;
  unreadCount?: number;
}

const roleLabelMap: Record<string, string> = {
  SYSTEM_ADMIN: 'System administrator',
  REGIONAL_OFFICER: 'Regional officer',
  BUREAU_OFFICER: 'Bureau officer',
  INSTITUTION_USER: 'Institution user'
};

export const Navbar: React.FC<NavbarProps> = ({
  user,
  onLogout,
  onNavigateAlerts,
  unreadCount = 0
}) => {
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleDateString('en-IN', {
          day: '2-digit', month: 'short', year: 'numeric', timeZone: 'Asia/Kolkata'
        }) + ' · ' + now.toLocaleTimeString('en-IN', {
          hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata'
        }) + ' IST'
      );
    };
    updateTime();
    const timer = window.setInterval(updateTime, 60_000);
    return () => window.clearInterval(timer);
  }, []);

  const initials = (user.display_name || 'User')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0].toUpperCase())
    .join('');

  return (
    <header className="app-header">
      <div className="app-header-inner">
        <div className="app-brand">
          <div className="app-brand-mark" aria-hidden="true">
            <ShieldCheck size={24} strokeWidth={1.8} />
          </div>
          <div className="app-brand-copy">
            <div className="app-brand-title-row">
              <span className="app-brand-title">Approval &amp; Compliance Workspace</span>
              <span className="app-brand-code">SIH26262</span>
            </div>
            <div className="app-brand-subtitle">Institutional workflow management</div>
          </div>
        </div>

        <div className="app-header-tools">
          <div className="app-prototype-label" title="This is an independent hackathon prototype">
            <span className="app-prototype-dot" />
            <span>DEMO PROTOTYPE</span>
          </div>

          <div className="app-clock" aria-label={`Current time ${timeStr}`}>
            <Clock3 size={15} aria-hidden="true" />
            <span>{timeStr}</span>
          </div>

          {user.role !== 'INSTITUTION_USER' && (
            <button
              type="button"
              onClick={onNavigateAlerts}
              className="app-icon-button app-notification-button"
              aria-label={`Open alerts${unreadCount > 0 ? `, ${unreadCount} unread` : ''}`}
              title="Alerts and escalations"
            >
              <Bell size={19} />
              {unreadCount > 0 && <span className="app-notification-count">{unreadCount > 9 ? '9+' : unreadCount}</span>}
            </button>
          )}

          <div className="app-profile" title={roleLabelMap[user.role] || user.role}>
            <div className="app-avatar" aria-hidden="true">{initials || <UserRound size={17} />}</div>
            <div className="app-profile-copy">
              <span className="app-profile-name">{user.display_name}</span>
              <span className="app-profile-role">{roleLabelMap[user.role] || user.role}</span>
            </div>
          </div>

          <button type="button" onClick={onLogout} className="app-icon-button app-logout-button" aria-label="Sign out" title="Sign out">
            <LogOut size={18} />
          </button>
        </div>
      </div>
      <div className="app-prototype-notice">
        <span>Independent SIH26262 prototype</span>
        <span className="notice-separator">•</span>
        <span>Not an official AICTE service · Synthetic demonstration data</span>
      </div>
    </header>
  );
};
