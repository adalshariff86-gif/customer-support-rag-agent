import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, SlidersHorizontal, Sun, Moon, Terminal, Volume2, ArrowDownCircle } from 'lucide-react';
import { useStore } from '../../store/useStore';

export const SettingsModal: React.FC = () => {
  const { 
    isSettingsOpen, 
    setSettingsOpen, 
    settings, 
    updateSettings, 
    developerMode, 
    setDeveloperMode,
    theme,
    setTheme 
  } = useStore();

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isSettingsOpen) {
        setSettingsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSettingsOpen, setSettingsOpen]);

  if (!isSettingsOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="w-full max-w-md rounded-2xl bg-white dark:bg-[#0F131C] border border-zinc-200/80 dark:border-zinc-800/80 shadow-2xl overflow-hidden font-sans text-zinc-900 dark:text-slate-100"
        >
          {/* Header */}
          <div className="px-6 py-4 bg-zinc-50 dark:bg-[#131722] border-b border-zinc-200/80 dark:border-zinc-800/80 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SlidersHorizontal className="w-4 h-4 text-indigo-500" />
              <h3 className="font-bold text-sm">RAG Engine Settings</h3>
            </div>
            <button
              onClick={() => setSettingsOpen(false)}
              className="p-1 rounded-lg text-zinc-400 hover:text-zinc-700 dark:hover:text-slate-200 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-6 text-xs">
            
            {/* LLM Temperature Slider */}
            <div className="space-y-2">
              <div className="flex justify-between font-mono">
                <label className="font-semibold text-zinc-700 dark:text-slate-300">
                  LLM Temperature ({settings.temperature})
                </label>
                <span className="text-zinc-400">
                  {settings.temperature <= 0.2 ? 'Strict Grounded' : 'Balanced'}
                </span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.0"
                step="0.05"
                value={settings.temperature}
                onChange={(e) => updateSettings({ temperature: parseFloat(e.target.value) })}
                className="w-full accent-indigo-600"
              />
              <p className="text-[11px] text-zinc-500 dark:text-slate-400">
                Lower values (0.0 - 0.2) ensure strict grounding in retrieved context documents.
              </p>
            </div>

            {/* Top-K Chunks Slider */}
            <div className="space-y-2">
              <div className="flex justify-between font-mono">
                <label className="font-semibold text-zinc-700 dark:text-slate-300">
                  Top-K Retrieved Chunks ({settings.top_k})
                </label>
                <span className="text-zinc-400">ChromaDB Vector Limit</span>
              </div>
              <input
                type="range"
                min="1"
                max="10"
                step="1"
                value={settings.top_k}
                onChange={(e) => updateSettings({ top_k: parseInt(e.target.value, 10) })}
                className="w-full accent-indigo-600"
              />
              <p className="text-[11px] text-zinc-500 dark:text-slate-400">
                Number of vector chunk citations sent to Gemini system prompt context window.
              </p>
            </div>

            {/* Developer Mode Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center gap-2.5">
                <Terminal className="w-4 h-4 text-emerald-500" />
                <div>
                  <span className="font-semibold block text-zinc-800 dark:text-slate-200">
                    Developer Telemetry Mode
                  </span>
                  <span className="text-[10px] text-zinc-400 dark:text-slate-500">
                    Displays latency, model telemetry, and cosine scores
                  </span>
                </div>
              </div>
              <input
                type="checkbox"
                checked={developerMode}
                onChange={(e) => setDeveloperMode(e.target.checked)}
                className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
              />
            </div>

            {/* Auto-Scroll Toggle */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
              <div className="flex items-center gap-2.5">
                <ArrowDownCircle className="w-4 h-4 text-indigo-500" />
                <span className="font-semibold text-zinc-800 dark:text-slate-200">
                  Auto-scroll to New Messages
                </span>
              </div>
              <input
                type="checkbox"
                checked={settings.auto_scroll}
                onChange={(e) => updateSettings({ auto_scroll: e.target.checked })}
                className="w-4 h-4 accent-indigo-600 rounded cursor-pointer"
              />
            </div>

            {/* Theme Selector */}
            <div className="space-y-2">
              <label className="font-semibold font-mono text-zinc-700 dark:text-slate-300">
                Interface Theme
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={() => setTheme('light')}
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                    theme === 'light'
                      ? 'bg-indigo-50 border-indigo-500 text-indigo-700'
                      : 'bg-zinc-50 dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-slate-300'
                  }`}
                >
                  <Sun className="w-4 h-4 text-amber-500" /> Light Theme
                </button>

                <button
                  onClick={() => setTheme('dark')}
                  className={`flex items-center justify-center gap-2 p-2.5 rounded-xl border text-xs font-semibold transition-all ${
                    theme === 'dark'
                      ? 'bg-indigo-950/60 border-indigo-500 text-indigo-300'
                      : 'bg-zinc-50 dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-slate-300'
                  }`}
                >
                  <Moon className="w-4 h-4 text-indigo-400" /> Dark Theme
                </button>
              </div>
            </div>

          </div>

          {/* Footer */}
          <div className="px-6 py-4 bg-zinc-50 dark:bg-[#131722] border-t border-zinc-200/80 dark:border-zinc-800/80 flex justify-end">
            <button
              onClick={() => setSettingsOpen(false)}
              className="px-5 py-2 rounded-xl bg-indigo-600 text-white font-semibold text-xs shadow-md hover:bg-indigo-500 transition-colors"
            >
              Save Preferences
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
