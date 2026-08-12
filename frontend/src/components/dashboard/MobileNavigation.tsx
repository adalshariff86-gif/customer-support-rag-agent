import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  MessageSquare, 
  Plus, 
  Database, 
  Terminal, 
  Settings, 
  X, 
  History, 
  Sun, 
  Moon,
  ChevronUp,
  Cpu,
  Home
} from 'lucide-react';
import { useStore } from '../../store/useStore';

export const MobileNavigation: React.FC = () => {
  const { 
    conversations, 
    activeConversationId, 
    switchConversation, 
    createNewConversation,
    setKnowledgeBaseOpen,
    setSettingsOpen,
    developerMode,
    toggleDeveloperMode,
    setDeveloperDrawerOpen,
    theme,
    setTheme,
    setActiveTab
  } = useStore();

  const [isHistorySheetOpen, setHistorySheetOpen] = useState(false);

  return (
    <>
      {/* Bottom Bar (Mobile Only: hidden on md+) */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-white/90 dark:bg-[#0D1017]/90 backdrop-blur-lg border-t border-zinc-200 dark:border-zinc-800 px-4 py-2 flex items-center justify-around font-sans">
        {/* New Chat */}
        <button
          onClick={() => createNewConversation()}
          className="flex flex-col items-center gap-0.5 text-indigo-600 dark:text-indigo-400 p-1"
        >
          <div className="p-2 rounded-full bg-indigo-600 text-white shadow-md">
            <Plus className="w-4 h-4" />
          </div>
          <span className="text-[10px] font-medium">New</span>
        </button>

        {/* Conversation History */}
        <button
          onClick={() => setHistorySheetOpen(true)}
          className="flex flex-col items-center gap-0.5 text-zinc-600 dark:text-slate-400 hover:text-zinc-900 dark:hover:text-white p-1"
        >
          <History className="w-5 h-5" />
          <span className="text-[10px] font-medium">History</span>
        </button>

        {/* Knowledge Store */}
        <button
          onClick={() => setKnowledgeBaseOpen(true)}
          className="flex flex-col items-center gap-0.5 text-zinc-600 dark:text-slate-400 hover:text-purple-500 p-1"
        >
          <Database className="w-5 h-5 text-purple-500" />
          <span className="text-[10px] font-medium">Docs</span>
        </button>

        {/* Telemetry Drawer */}
        <button
          onClick={() => setDeveloperDrawerOpen(true)}
          className={`flex flex-col items-center gap-0.5 p-1 ${
            developerMode ? 'text-emerald-500' : 'text-zinc-600 dark:text-slate-400'
          }`}
        >
          <Terminal className="w-5 h-5" />
          <span className="text-[10px] font-medium">Telemetry</span>
        </button>

        {/* Settings */}
        <button
          onClick={() => setSettingsOpen(true)}
          className="flex flex-col items-center gap-0.5 text-zinc-600 dark:text-slate-400 hover:text-zinc-900 dark:hover:text-white p-1"
        >
          <Settings className="w-5 h-5" />
          <span className="text-[10px] font-medium">Settings</span>
        </button>
      </div>

      {/* History Bottom Sheet (Mobile) */}
      <AnimatePresence>
        {isHistorySheetOpen && (
          <div className="fixed inset-0 z-50 md:hidden bg-black/60 backdrop-blur-sm flex flex-col justify-end">
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="bg-white dark:bg-[#0F131C] border-t border-zinc-200 dark:border-zinc-800 rounded-t-3xl max-h-[80vh] flex flex-col overflow-hidden shadow-2xl"
            >
              <div className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="w-4 h-4 text-indigo-500" />
                  <h3 className="font-bold text-sm text-zinc-900 dark:text-slate-100">
                    Conversation History ({conversations.length})
                  </h3>
                </div>
                <button
                  onClick={() => setHistorySheetOpen(false)}
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-700 dark:hover:text-slate-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {conversations.map((conv) => {
                  const isActive = conv.id === activeConversationId;
                  return (
                    <button
                      key={conv.id}
                      onClick={() => {
                        switchConversation(conv.id);
                        setHistorySheetOpen(false);
                      }}
                      className={`w-full text-left p-3 rounded-2xl transition-all border ${
                        isActive
                          ? 'bg-indigo-50 dark:bg-indigo-950/40 border-indigo-500 text-indigo-900 dark:text-indigo-200 font-semibold'
                          : 'bg-zinc-50 dark:bg-zinc-900/60 border-zinc-200/80 dark:border-zinc-800 text-zinc-700 dark:text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs truncate font-bold">{conv.title}</span>
                        <span className="text-[10px] font-mono text-zinc-400">{conv.last_message_at}</span>
                      </div>
                      <p className="text-[11px] text-zinc-500 dark:text-slate-400 truncate mt-1">
                        {conv.preview_text}
                      </p>
                    </button>
                  );
                })}
              </div>

              <div className="p-4 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-[#131722] flex justify-between items-center text-xs font-mono">
                <button
                  onClick={() => {
                    setActiveTab('landing');
                    setHistorySheetOpen(false);
                  }}
                  className="flex items-center gap-1.5 text-zinc-500 hover:text-zinc-900 dark:hover:text-slate-200"
                >
                  <Home className="w-4 h-4" /> Landing Overview
                </button>
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className="p-2 rounded-xl bg-zinc-200 dark:bg-zinc-800"
                >
                  {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4" />}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};
