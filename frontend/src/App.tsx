import React, { useState, useEffect } from 'react';
import { User, NotificationItem } from './types';
import { api, getStoredUser, clearToken } from './services/api';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { LoginPage } from './pages/LoginPage';
import { ControlTowerPage } from './pages/ControlTowerPage';
import { ApplicationsPage } from './pages/ApplicationsPage';
import { CaseWorkbenchPage } from './pages/CaseWorkbenchPage';
import { EvcPage } from './pages/EvcPage';
import { CompliancePage } from './pages/CompliancePage';
import { DocumentsPage } from './pages/DocumentsPage';
import { AlertsPage } from './pages/AlertsPage';
import { AuditPage } from './pages/AuditPage';
import { WorkflowConfigPage } from './pages/WorkflowConfigPage';
import { AIReviewPage } from './pages/AIReviewPage';

export const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(getStoredUser());
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);
  const [initialStageFilter, setInitialStageFilter] = useState<string | undefined>(undefined);
  const [unreadAlerts, setUnreadAlerts] = useState<number>(0);
  const [loadingUser, setLoadingUser] = useState<boolean>(true);

  // Check auth session
  useEffect(() => {
    const checkSession = async () => {
      try {
        const me = await api.getMe();
        setUser(me);
        // Load initial unread alert count
        const alerts = await api.listAlerts(undefined, 'UNREAD');
        setUnreadAlerts(alerts.length);
      } catch (_) {
        setUser(null);
      } finally {
        setLoadingUser(false);
      }
    };
    checkSession();
  }, []);

  // Keep the navbar alert badge synchronized across independently logged-in demo sessions.
  useEffect(() => {
    if (!user) return;
    const refreshUnread = async () => {
      try {
        const alerts = await api.listAlerts(undefined, 'UNREAD');
        setUnreadAlerts(alerts.length);
      } catch (_) {
        // A transient refresh failure should not interrupt the active workspace.
      }
    };
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') void refreshUnread();
    }, 8000);
    return () => window.clearInterval(timer);
  }, [user?.id]);

  const handleLogout = async () => {
    await api.logout();
    setUser(null);
    setCurrentTab('overview');
    setSelectedAppId(null);
  };

  const handleSelectApplication = (id: string) => {
    setSelectedAppId(id);
    setCurrentTab('workbench');
  };

  const handleNavigateApplications = (stage?: string) => {
    setInitialStageFilter(stage);
    setSelectedAppId(null);
    setCurrentTab('applications');
  };

  const handleNavigateAlerts = () => {
    setSelectedAppId(null);
    setCurrentTab('alerts');
  };

  if (loadingUser) {
    return (
      <div className="app-loading-screen min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-white text-sm font-semibold flex items-center gap-3">
          <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span>Verifying Administrative Session...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onLoginSuccess={u => setUser(u)} />;
  }

  return (
    <div className="app-shell min-h-screen flex flex-col font-sans">
      <Navbar
        user={user}
        onLogout={handleLogout}
        onNavigateAlerts={handleNavigateAlerts}
        unreadCount={unreadAlerts}
      />

      <div className="app-body flex flex-1">
        <Sidebar
          currentTab={currentTab === 'workbench' ? 'applications' : currentTab}
          onSelectTab={tab => {
            const institutionTabs = new Set(['overview', 'applications', 'documents', 'ai']);
            const officerTabs = new Set(['overview', 'applications', 'evc', 'compliance', 'documents', 'ai', 'alerts', 'audit', 'config']);
            if (!(user.role === 'INSTITUTION_USER' ? institutionTabs : officerTabs).has(tab)) return;
            setSelectedAppId(null);
            setCurrentTab(tab);
          }}
          userRole={user.role}
          unreadAlertsCount={unreadAlerts}
        />

        <main className="app-main flex-1 overflow-x-hidden">
          {currentTab === 'overview' && (
            <ControlTowerPage
              user={user}
              onNavigateApplications={handleNavigateApplications}
              onNavigateAlerts={handleNavigateAlerts}
              onSelectApplication={handleSelectApplication}
            />
          )}

          {currentTab === 'applications' && (
            <ApplicationsPage
              user={user}
              initialStageFilter={initialStageFilter}
              onSelectApplication={handleSelectApplication}
            />
          )}

          {currentTab === 'workbench' && selectedAppId && (
            <CaseWorkbenchPage
              applicationId={selectedAppId}
              user={user}
              onBack={() => setCurrentTab('applications')}
            />
          )}

          {user.role !== 'INSTITUTION_USER' && currentTab === 'evc' && (
            <EvcPage
              user={user}
              onOpenCase={handleSelectApplication}
            />
          )}

          {user.role !== 'INSTITUTION_USER' && currentTab === 'compliance' && (
            <CompliancePage
              user={user}
              onOpenCase={handleSelectApplication}
            />
          )}

          {currentTab === 'documents' && (
            <DocumentsPage user={user} />
          )}

          {currentTab === 'ai' && (
            <AIReviewPage user={user} />
          )}

          {user.role !== 'INSTITUTION_USER' && currentTab === 'alerts' && (
            <AlertsPage
              user={user}
              onOpenCase={handleSelectApplication}
            />
          )}

          {user.role !== 'INSTITUTION_USER' && currentTab === 'audit' && (
            <AuditPage
              user={user}
              onOpenCase={handleSelectApplication}
            />
          )}

          {user.role === 'SYSTEM_ADMIN' && currentTab === 'config' && (
            <WorkflowConfigPage user={user} />
          )}
        </main>
      </div>
    </div>
  );
};
