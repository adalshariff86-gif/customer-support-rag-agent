import React from 'react';
import { 
  Sparkles, 
  Terminal, 
  BookOpen, 
  Sliders, 
  Database, 
  ShieldCheck,
  Cpu,
  SlidersHorizontal,
  ChevronDown
} from 'lucide-react';
import { useStore } from '../../store/useStore';

export const Header: React.FC = () => {
  const { 
    conversations, 
    activeConversationId, 
    developerMode, 
    toggleDeveloperMode,
    isSourcesPanelOpen,
    setSourcesPanelOpen,
    isDeveloperDrawerOpen,
    setDeveloperDrawerOpen,
    setSettingsOpen,
    messages
  } = useStore();

  const activeSession = conversations.find((c) => c.id === activeConversationId);

  // Count total sources from last assistant message
  const lastAssistantMessage = [...messages].reverse().find((m) => m.role === 'assistant');
  const sourcesCount = lastAssistantMessage?.sources?.length || 0;

  return (
    <header className="h-14 px-4 bg-white/90 dark:bg-[#0A0C10]/90 border-b border-zinc-200/80 dark:border-zinc-800/80 flex items-center justify-between backdrop-blur-md sticky top-0 z-20 font-sans">
      
      {/* Left: Active Session Info */}
      <div className="flex items-center gap-3">
        <div className="flex flex-col">
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-slate-100 truncate max-w-xs sm:max-w-md">
            {activeSession?.title || 'Active Session'}
          </h2>
          <div className="flex items-center gap-2 text-[10px] font-mono text-zinc-400 dark:text-slate-500">
            <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              ChromaDB RAG
            </span>
            <span>•</span>
            <span>Gemini 3.5 Flash</span>
          </div>
        </div>
      </div>

      {/* Right: Actions & Panel Toggles */}
      <div className="flex items-center gap-2">
        {/* Developer Drawer Toggle */}
        {developerMode && (
          <button
            onClick={() => setDeveloperDrawerOpen(!isDeveloperDrawerOpen)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
              isDeveloperDrawerOpen
                ? 'bg-emerald-500/20 text-emerald-600 dark:text-emerald-300 border border-emerald-500/40'
                : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-slate-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
            }`}
            title="Inspect RAG Latency & Metrics Drawer"
          >
            <Terminal className="w-3.5 h-3.5 text-emerald-500" />
            <span className="hidden sm:inline">Metrics</span>
          </button>
        )}

        {/* Sources Panel Drawer Toggle */}
        <button
          onClick={() => setSourcesPanelOpen(!isSourcesPanelOpen)}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            isSourcesPanelOpen
              ? 'bg-indigo-500/20 text-indigo-600 dark:text-indigo-300 border border-indigo-500/40'
              : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-slate-300 hover:bg-zinc-200 dark:hover:bg-zinc-700'
          }`}
          title="Toggle Cited Document Sources Drawer"
        >
          <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
          <span className="hidden sm:inline">Sources</span>
          {sourcesCount > 0 && (
            <span className="px-1.5 py-0.2 rounded-full text-[10px] font-mono bg-indigo-600 text-white font-bold">
              {sourcesCount}
            </span>
          )}
        </button>

        {/* Settings button */}
        <button
          onClick={() => setSettingsOpen(true)}
          className="p-1.5 rounded-lg text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          title="RAG Hyperparameters Settings"
        >
          <SlidersHorizontal className="w-4 h-4" />
        </button>
      </div>

    </header>
  );
};
