import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Search, 
  Plus, 
  MessageSquare, 
  SlidersHorizontal, 
  Terminal, 
  BookOpen, 
  Database, 
  Sun, 
  Moon, 
  Home, 
  X,
  Command,
  ArrowRight
} from 'lucide-react';
import { useStore } from '../../store/useStore';

export const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const { 
    conversations, 
    switchConversation, 
    createNewConversation, 
    setSettingsOpen, 
    setKnowledgeBaseOpen, 
    setSourcesPanelOpen,
    toggleDeveloperMode, 
    developerMode,
    theme, 
    setTheme, 
    activeTab, 
    setActiveTab 
  } = useStore();

  // Listen for CMD+K / CTRL+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      } else if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Command items definition
  const actionCommands = [
    {
      id: 'cmd-new-chat',
      title: 'New Chat Session',
      category: 'Actions',
      icon: Plus,
      badge: 'CMD + N',
      action: () => {
        createNewConversation();
        if (activeTab !== 'app') setActiveTab('app');
      },
    },
    {
      id: 'cmd-settings',
      title: 'RAG Hyperparameter Settings',
      category: 'Actions',
      icon: SlidersHorizontal,
      badge: 'Settings',
      action: () => {
        setSettingsOpen(true);
        if (activeTab !== 'app') setActiveTab('app');
      },
    },
    {
      id: 'cmd-knowledge-base',
      title: 'Manage Support Knowledge Base',
      category: 'Actions',
      icon: Database,
      badge: 'ChromaDB',
      action: () => {
        setKnowledgeBaseOpen(true);
        if (activeTab !== 'app') setActiveTab('app');
      },
    },
    {
      id: 'cmd-sources',
      title: 'View Citation Sources Drawer',
      category: 'Actions',
      icon: BookOpen,
      badge: 'Sources',
      action: () => {
        setSourcesPanelOpen(true);
        if (activeTab !== 'app') setActiveTab('app');
      },
    },
    {
      id: 'cmd-dev-mode',
      title: `Toggle Developer Telemetry (${developerMode ? 'Enabled' : 'Disabled'})`,
      category: 'Preferences',
      icon: Terminal,
      badge: developerMode ? 'ON' : 'OFF',
      action: () => toggleDeveloperMode(),
    },
    {
      id: 'cmd-theme',
      title: `Switch Theme (Current: ${theme})`,
      category: 'Preferences',
      icon: theme === 'dark' ? Sun : Moon,
      badge: theme === 'dark' ? 'Light' : 'Dark',
      action: () => setTheme(theme === 'dark' ? 'light' : 'dark'),
    },
    {
      id: 'cmd-nav-overview',
      title: 'Go to Landing Page Overview',
      category: 'Navigation',
      icon: Home,
      badge: 'Overview',
      action: () => setActiveTab('landing'),
    },
    {
      id: 'cmd-nav-app',
      title: 'Go to Workspace Dashboard',
      category: 'Navigation',
      icon: MessageSquare,
      badge: 'Workspace',
      action: () => setActiveTab('app'),
    },
  ];

  // Conversation items mapped to command list
  const conversationCommands = conversations.map((conv) => ({
    id: `conv-${conv.id}`,
    title: conv.title,
    category: 'Conversations',
    icon: MessageSquare,
    badge: conv.message_count + ' msgs',
    action: () => {
      switchConversation(conv.id);
      if (activeTab !== 'app') setActiveTab('app');
    },
  }));

  const allItems = [...actionCommands, ...conversationCommands];

  const filteredItems = allItems.filter(
    (item) =>
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      item.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleKeyDownInMenu = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filteredItems.length));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredItems.length) % Math.max(1, filteredItems.length));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredItems[selectedIndex]) {
        filteredItems[selectedIndex].action();
        setIsOpen(false);
      }
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/60 backdrop-blur-sm font-sans">
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: -10 }}
          transition={{ duration: 0.15 }}
          className="w-full max-w-xl rounded-2xl bg-white dark:bg-[#0F131C] border border-zinc-200/90 dark:border-zinc-800/90 shadow-2xl overflow-hidden text-zinc-900 dark:text-slate-100"
        >
          {/* Top Search Input */}
          <div className="px-4 py-3 border-b border-zinc-200/80 dark:border-zinc-800/80 flex items-center gap-3">
            <Search className="w-4 h-4 text-zinc-400 shrink-0" />
            <input
              ref={inputRef}
              type="text"
              placeholder="Type a command or search conversations... (CMD + K)"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setSelectedIndex(0);
              }}
              onKeyDown={handleKeyDownInMenu}
              className="w-full bg-transparent text-sm text-zinc-900 dark:text-slate-100 placeholder-zinc-400 focus:outline-none"
            />
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-md text-zinc-400 hover:text-zinc-600 dark:hover:text-slate-200"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Results List */}
          <div className="max-h-80 overflow-y-auto p-2 space-y-1">
            {filteredItems.length === 0 ? (
              <div className="p-6 text-center text-xs text-zinc-400 dark:text-slate-500 font-mono">
                No matching actions or conversations found for "{query}".
              </div>
            ) : (
              filteredItems.map((item, index) => {
                const IconComponent = item.icon;
                const isSelected = index === selectedIndex;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      item.action();
                      setIsOpen(false);
                    }}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`w-full px-3 py-2.5 rounded-xl flex items-center justify-between text-xs transition-colors ${
                      isSelected
                        ? 'bg-indigo-600 text-white font-medium'
                        : 'text-zinc-700 dark:text-slate-300 hover:bg-zinc-100 dark:hover:bg-zinc-800/70'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 truncate">
                      <IconComponent
                        className={`w-4 h-4 shrink-0 ${
                          isSelected ? 'text-white' : 'text-indigo-500'
                        }`}
                      />
                      <span className="truncate">{item.title}</span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span
                        className={`px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold ${
                          isSelected
                            ? 'bg-indigo-700 text-indigo-100'
                            : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-slate-400'
                        }`}
                      >
                        {item.badge}
                      </span>
                      {isSelected && <ArrowRight className="w-3.5 h-3.5 text-white" />}
                    </div>
                  </button>
                );
              })
            )}
          </div>

          {/* Footer Shortcuts hint */}
          <div className="px-4 py-2 bg-zinc-50 dark:bg-[#131722] border-t border-zinc-200/80 dark:border-zinc-800/80 flex items-center justify-between text-[10px] font-mono text-zinc-400 dark:text-slate-500">
            <div className="flex items-center gap-3">
              <span><kbd className="px-1 py-0.5 bg-zinc-200 dark:bg-zinc-800 rounded">↑</kbd> <kbd className="px-1 py-0.5 bg-zinc-200 dark:bg-zinc-800 rounded">↓</kbd> Navigate</span>
              <span><kbd className="px-1 py-0.5 bg-zinc-200 dark:bg-zinc-800 rounded">↵</kbd> Select</span>
            </div>
            <span><kbd className="px-1 py-0.5 bg-zinc-200 dark:bg-zinc-800 rounded">ESC</kbd> Close</span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
