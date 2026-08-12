import React, { useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ChatArea } from './ChatArea';
import { SourcesPanel } from './SourcesPanel';
import { DeveloperDrawer } from './DeveloperDrawer';
import { SettingsModal } from './SettingsModal';
import { KnowledgeBaseModal } from './KnowledgeBaseModal';
import { MobileNavigation } from './MobileNavigation';
import { useStore } from '../../store/useStore';

export const Dashboard: React.FC = () => {
  const { fetchHealthStatus, fetchDocuments } = useStore();

  useEffect(() => {
    fetchHealthStatus();
    fetchDocuments();
  }, []);

  return (
    <div className="flex h-screen bg-white dark:bg-[#0A0C10] text-zinc-900 dark:text-slate-100 overflow-hidden font-sans selection:bg-indigo-500 selection:text-white transition-colors duration-200">
      {/* Left Sidebar (Desktop) */}
      <Sidebar />

      {/* Main Chat Workspace */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden pb-14 md:pb-0">
        <Header />
        <div className="flex-1 flex overflow-hidden relative">
          <ChatArea />
          <SourcesPanel />
        </div>
      </div>

      {/* Mobile Navigation Bar & Sheets */}
      <MobileNavigation />

      {/* Telemetry & Modals */}
      <DeveloperDrawer />
      <SettingsModal />
      <KnowledgeBaseModal />
    </div>
  );
};
