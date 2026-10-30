import React from 'react';
import {
  LayoutDashboard,
  FileText,
  CalendarDays,
  ShieldCheck,
  FolderLock,
  BellRing,
  History,
  SlidersHorizontal,
  CircleHelp,
  Bot
} from 'lucide-react';
import { Role } from '../types';

interface SidebarProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  userRole: Role;
  unreadAlertsCount?: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  userRole,
  unreadAlertsCount = 0
}) => {
  const menuItems = userRole === 'INSTITUTION_USER'
    ? [
        { id: 'overview', label: 'My overview', icon: LayoutDashboard, group: 'MY INSTITUTION' },
        { id: 'applications', label: 'My applications', icon: FileText, group: 'MY INSTITUTION' },
        { id: 'documents', label: 'Forms & documents', icon: FolderLock, group: 'MY INSTITUTION' },
        { id: 'ai', label: 'Regulatory AI', icon: Bot, group: 'MY INSTITUTION' }
      ]
    : [
        { id: 'overview', label: 'Operations overview', icon: LayoutDashboard, group: 'WORKSPACE' },
        { id: 'applications', label: 'Applications', icon: FileText, group: 'WORKSPACE' },
        { id: 'evc', label: 'EVC schedule', icon: CalendarDays, group: 'WORKSPACE' },
        { id: 'compliance', label: 'Compliance', icon: ShieldCheck, group: 'WORKSPACE' },
        { id: 'documents', label: 'Documents & forms', icon: FolderLock, group: 'WORKSPACE' },
        { id: 'ai', label: 'Regulatory AI', icon: Bot, group: 'WORKSPACE' },
        { id: 'alerts', label: 'Alerts & escalations', icon: BellRing, group: 'GOVERNANCE', badge: unreadAlertsCount },
        { id: 'audit', label: 'Audit trail', icon: History, group: 'GOVERNANCE' }
      ];

  if (userRole === 'SYSTEM_ADMIN') {
    menuItems.push({ id: 'config', label: 'Workflow configuration', icon: SlidersHorizontal, group: 'ADMINISTRATION', badge: undefined });
  }

  let lastGroup = '';

  return (
    <aside className="app-sidebar" aria-label="Primary navigation">
      <div className="sidebar-context">
        <div className="sidebar-context-label">WORKSPACE</div>
        <div className="sidebar-context-title">{userRole === 'INSTITUTION_USER' ? 'Institution portal' : 'Approval operations'}</div>
        <div className="sidebar-context-subtitle">{userRole === 'INSTITUTION_USER' ? 'Your applications and documents only' : 'Monitor cases and obligations'}</div>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map(item => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          const showGroup = item.group !== lastGroup;
          lastGroup = item.group;
          return (
            <React.Fragment key={item.id}>
              {showGroup && <div className="sidebar-group-label">{item.group}</div>}
              <button
                type="button"
                onClick={() => onSelectTab(item.id)}
                className={`sidebar-nav-item${isActive ? ' is-active' : ''}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="sidebar-nav-icon" size={18} strokeWidth={1.8} aria-hidden="true" />
                <span className="sidebar-nav-label">{item.label}</span>
                {item.badge !== undefined && item.badge > 0 && (
                  <span className="sidebar-nav-badge" aria-label={`${item.badge} unread alerts`}>
                    {item.badge > 99 ? '99+' : item.badge}
                  </span>
                )}
              </button>
            </React.Fragment>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-footer-icon"><CircleHelp size={16} /></div>
        <div>
          <div className="sidebar-footer-title">Demonstration environment</div>
          <div className="sidebar-footer-caption">Synthetic data · SIH26262</div>
        </div>
      </div>
    </aside>
  );
};
