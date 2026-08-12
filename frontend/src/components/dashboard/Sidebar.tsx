import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Plus, 
  MessageSquare, 
  Search, 
  Settings, 
  Terminal, 
  BookOpen, 
  Sun, 
  Moon, 
  ChevronLeft, 
  ChevronRight, 
  ShieldCheck, 
  Cpu,
  Home,
  Trash2,
  Database
} from 'lucide-react';
import { useStore } from '../../store/useStore';

export const Sidebar: React.FC = () => {
  const { 
    conversations, 
    activeConversationId, 
    switchConversation, 
    createNewConversation, 
    isSidebarCollapsed, 
    toggleSidebar,
    developerMode,
    toggleDeveloperMode,
    isSettingsOpen,
    setSettingsOpen,
    isKnowledgeBaseOpen,
    setKnowledgeBaseOpen,
    healthStatus,
    theme,
    setTheme,
    setActiveTab
  } = useStore();

  const [searchQuery, setSearchQuery] = useState('');

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.preview_text.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const toggleTheme = () => {
    if (theme === 'dark') setTheme('light');
    else setTheme('dark');
  };

  return (
    <aside 
      className={`hidden md:flex relative h-screen bg-zinc-50 dark:bg-[#0B0E14] border-r border-zinc-200/80 dark:border-zinc-800/80 flex-col justify-between transition-all duration-300 z-30 font-sans ${
        isSidebarCollapsed ? 'w-16' : 'w-72'
      }`}
    >
      {/* Top Header & Brand */}
      <div className="p-3 space-y-3">
        <div className="flex items-center justify-between">
          {!isSidebarCollapsed && (
            <div 
              onClick={() => setActiveTab('landing')}
              className="flex items-center gap-2.5 cursor-pointer group"
            >
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#5B5CEB] to-[#3B82F6] dark:from-[#7C6CFF] dark:to-[#60A5FA] flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform">
                <Cpu className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="font-bold text-sm tracking-tight text-zinc-900 dark:text-slate-100">
                  ResolveHQ
                </span>
                <span className="text-[10px] font-mono text-zinc-400 dark:text-slate-500">
                  v3.5 RAG Engine
                </span>
              </div>
            </div>
          )}

          {isSidebarCollapsed && (
            <div 
              onClick={() => setActiveTab('landing')}
              className="w-9 h-9 mx-auto rounded-xl bg-gradient-to-tr from-[#5B5CEB] to-[#3B82F6] flex items-center justify-center text-white cursor-pointer"
            >
              <Cpu className="w-4 h-4" />
            </div>
          )}

          <button
            onClick={toggleSidebar}
            className="p-1.5 rounded-lg text-zinc-500 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 transition-colors"
            title={isSidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          >
            {isSidebarCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* New Chat Button */}
        <button
          onClick={() => createNewConversation()}
          className={`w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs shadow-md shadow-indigo-500/20 transition-all ${
            isSidebarCollapsed ? 'p-2.5' : ''
          }`}
          title="Start New Conversation"
        >
          <Plus className="w-4 h-4" />
          {!isSidebarCollapsed && <span>New Conversation</span>}
        </button>

        {/* Search input (when expanded) */}
        {!isSidebarCollapsed && (
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-zinc-400 dark:text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search conversations..."
              className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-zinc-200/60 dark:bg-zinc-900 border border-zinc-200/80 dark:border-zinc-800 text-xs text-zinc-900 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-sans"
            />
          </div>
        )}
      </div>

      {/* Conversation Sessions List */}
      <div className="flex-1 overflow-y-auto px-2 space-y-1 py-1">
        {!isSidebarCollapsed && (
          <div className="px-2 py-1 text-[10px] font-mono uppercase tracking-wider text-zinc-400 dark:text-slate-500 font-semibold">
            History
          </div>
        )}

        {filteredConversations.map((session) => {
          const isActive = session.id === activeConversationId;
          return (
            <button
              key={session.id}
              onClick={() => switchConversation(session.id)}
              className={`w-full text-left p-2 rounded-xl transition-all flex items-center gap-2.5 ${
                isActive
                  ? 'bg-white dark:bg-[#131722] text-zinc-900 dark:text-slate-100 font-semibold border border-zinc-200 dark:border-zinc-800 shadow-sm'
                  : 'text-zinc-600 dark:text-slate-400 hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50'
              }`}
              title={session.title}
            >
              <MessageSquare className={`w-4 h-4 shrink-0 ${isActive ? 'text-indigo-600 dark:text-indigo-400' : 'opacity-60'}`} />
              {!isSidebarCollapsed && (
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-xs truncate font-medium">{session.title}</p>
                    <span className="text-[10px] font-mono opacity-60 ml-1">{session.last_message_at}</span>
                  </div>
                  <p className="text-[11px] opacity-60 truncate font-sans">{session.preview_text}</p>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Controls & System Status */}
      <div className="p-3 border-t border-zinc-200/80 dark:border-zinc-800/80 space-y-2 font-sans">
        
        {/* Knowledge Base Launcher */}
        <button
          onClick={() => setKnowledgeBaseOpen(true)}
          className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-medium text-zinc-700 dark:text-slate-300 hover:bg-zinc-200/60 dark:hover:bg-zinc-800/60 transition-colors ${
            isSidebarCollapsed ? 'justify-center' : ''
          }`}
          title="Open Knowledge Base Vector Store"
        >
          <Database className="w-4 h-4 text-purple-500 shrink-0" />
          {!isSidebarCollapsed && <span>Knowledge Base Docs</span>}
        </button>

        {/* Developer Mode Toggle */}
        <button
          onClick={toggleDeveloperMode}
          className={`w-full flex items-center justify-between px-2.5 py-2 rounded-xl text-xs font-medium transition-colors ${
            developerMode 
              ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' 
              : 'text-zinc-600 dark:text-slate-400 hover:bg-zinc-200/60 dark:hover:bg-zinc-800/60'
          } ${isSidebarCollapsed ? 'justify-center' : ''}`}
          title="Toggle Developer Mode Metrics"
        >
          <div className="flex items-center gap-2.5">
            <Terminal className="w-4 h-4 shrink-0" />
            {!isSidebarCollapsed && <span>Developer Mode</span>}
          </div>
          {!isSidebarCollapsed && (
            <span className={`w-2 h-2 rounded-full ${developerMode ? 'bg-emerald-500 animate-pulse' : 'bg-zinc-400'}`} />
          )}
        </button>

        {/* Settings Modal Trigger */}
        <button
          onClick={() => setSettingsOpen(true)}
          className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-medium text-zinc-700 dark:text-slate-300 hover:bg-zinc-200/60 dark:hover:bg-zinc-800/60 transition-colors ${
            isSidebarCollapsed ? 'justify-center' : ''
          }`}
          title="RAG Engine Settings"
        >
          <Settings className="w-4 h-4 shrink-0 text-zinc-500" />
          {!isSidebarCollapsed && <span>Settings</span>}
        </button>

        {/* Return to Overview & Theme Switcher */}
        <div className="pt-2 border-t border-zinc-200/60 dark:border-zinc-800/60 flex items-center justify-between">
          <button
            onClick={() => setActiveTab('landing')}
            className={`flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-900 dark:hover:text-slate-200 font-mono ${
              isSidebarCollapsed ? 'hidden' : ''
            }`}
          >
            <Home className="w-3.5 h-3.5" /> Landing
          </button>

          <button
            onClick={toggleTheme}
            className="p-1.5 rounded-lg text-zinc-600 dark:text-slate-400 hover:bg-zinc-200/60 dark:hover:bg-zinc-800 transition-colors"
            title="Toggle Theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-zinc-700" />}
          </button>
        </div>

        {/* Health status pill */}
        {!isSidebarCollapsed && healthStatus && (
          <div className="p-2 rounded-xl bg-zinc-200/50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 flex items-center justify-between text-[10px] font-mono">
            <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
              <ShieldCheck className="w-3.5 h-3.5" /> ChromaDB Connected
            </span>
            <span className="text-zinc-500 dark:text-slate-400">{healthStatus.tests_passing} Tests</span>
          </div>
        )}
      </div>
    </aside>
  );
};
