import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, BookOpen, ExternalLink, FileText, CheckCircle2, Copy, Layers } from 'lucide-react';
import { useStore } from '../../store/useStore';

export const SourcesPanel: React.FC = () => {
  const { 
    isSourcesPanelOpen, 
    setSourcesPanelOpen, 
    selectedSource, 
    setSelectedSource,
    messages 
  } = useStore();

  // If no specific source selected, grab all sources from last assistant message
  const lastAssistantMessage = [...messages].reverse().find((m) => m.role === 'assistant');
  const allSources = lastAssistantMessage?.sources || [];

  const activeSource = selectedSource || allSources[0];

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isSourcesPanelOpen) {
        setSourcesPanelOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isSourcesPanelOpen, setSourcesPanelOpen]);

  if (!isSourcesPanelOpen) return null;

  return (
    <AnimatePresence>
      <motion.aside
        initial={{ x: 320, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        exit={{ x: 320, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="w-80 h-[calc(100vh-3.5rem)] bg-zinc-50 dark:bg-[#0D1017] border-l border-zinc-200/80 dark:border-zinc-800/80 flex flex-col justify-between z-20 font-sans shadow-xl overflow-hidden"
      >
        {/* Panel Header */}
        <div className="p-4 bg-white/80 dark:bg-[#11151F]/80 border-b border-zinc-200/80 dark:border-zinc-800/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-indigo-500" />
            <h3 className="font-semibold text-xs text-zinc-900 dark:text-slate-100 uppercase tracking-wider font-mono">
              Source Citations
            </h3>
          </div>
          <button
            onClick={() => setSourcesPanelOpen(false)}
            className="p-1 rounded-lg text-zinc-400 hover:text-zinc-700 dark:hover:text-slate-200 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Source List selector */}
        {allSources.length > 0 && (
          <div className="px-3 py-2 bg-zinc-100/60 dark:bg-zinc-900/60 border-b border-zinc-200/60 dark:border-zinc-800/60 flex items-center gap-1.5 overflow-x-auto text-[11px] font-mono">
            {allSources.map((src, idx) => {
              const isSelected = activeSource?.id === src.id;
              return (
                <button
                  key={src.id || idx}
                  onClick={() => setSelectedSource(src)}
                  className={`px-2.5 py-1 rounded-md transition-all shrink-0 ${
                    isSelected
                      ? 'bg-indigo-600 text-white font-semibold'
                      : 'bg-zinc-200/80 dark:bg-zinc-800 text-zinc-700 dark:text-slate-300 hover:bg-zinc-300'
                  }`}
                >
                  Chunk #{idx + 1}
                </button>
              );
            })}
          </div>
        )}

        {/* Selected Source Detail View */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs font-sans">
          {activeSource ? (
            <div className="space-y-4">
              {/* Score pill */}
              <div className="p-3 rounded-xl bg-white dark:bg-[#11151F] border border-zinc-200 dark:border-zinc-800 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[10px] text-zinc-400 dark:text-slate-500 font-semibold uppercase">
                    Cosine Similarity
                  </span>
                  <span className="font-mono font-bold text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    {typeof activeSource.score === 'number' ? (activeSource.score <= 1.0 ? (activeSource.score * 100).toFixed(2) : activeSource.score.toFixed(2)) : '0'}% Match
                  </span>
                </div>
                <div className="h-1.5 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full"
                    style={{ width: `${typeof activeSource.score === 'number' ? (activeSource.score <= 1.0 ? activeSource.score * 100 : activeSource.score) : 0}%` }}
                  />
                </div>
              </div>

              {/* Document Info */}
              <div className="space-y-1.5">
                <span className="text-[10px] font-mono text-zinc-400 dark:text-slate-500 uppercase font-semibold">
                  Document Title
                </span>
                <p className="font-bold text-zinc-900 dark:text-slate-100 text-sm">
                  {activeSource.metadata?.source || activeSource.metadata?.filename || activeSource.metadata?.document_name || activeSource.metadata?.title || 'Retrieved Source'}
                </p>
              </div>

              {/* Metadata Fields */}
              <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                <div className="p-2.5 rounded-xl bg-white dark:bg-[#11151F] border border-zinc-200 dark:border-zinc-800 space-y-0.5">
                  <span className="text-zinc-400 dark:text-slate-500">Section:</span>
                  <p className="font-semibold text-zinc-800 dark:text-slate-200 truncate">
                    {activeSource.metadata?.section || 'General'}
                  </p>
                </div>
                <div className="p-2.5 rounded-xl bg-white dark:bg-[#11151F] border border-zinc-200 dark:border-zinc-800 space-y-0.5">
                  <span className="text-zinc-400 dark:text-slate-500">Chunk ID:</span>
                  <p className="font-semibold text-zinc-800 dark:text-slate-200 font-mono truncate">
                    {activeSource.id || 'chunk-01'}
                  </p>
                </div>
              </div>

              {/* Extracted Chunk Text */}
              <div className="space-y-1.5">
                <span className="text-[10px] font-mono text-zinc-400 dark:text-slate-500 uppercase font-semibold">
                  Indexed Vector Chunk Content
                </span>
                <div className="p-3.5 rounded-xl bg-white dark:bg-[#11151F] border border-zinc-200 dark:border-zinc-800 font-mono text-[11px] text-zinc-800 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                  {activeSource.content}
                </div>
              </div>

              {/* Source URL link */}
              {activeSource.metadata?.source_url && (
                <a
                  href={activeSource.metadata.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between p-2.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/50 text-xs font-mono font-medium hover:underline"
                >
                  <span>Open Documentation Page</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-zinc-400 dark:text-slate-500 font-mono text-xs">
              No citation selected. Send a query to inspect vector chunks.
            </div>
          )}
        </div>

        {/* Panel Footer */}
        <div className="p-3 bg-white/80 dark:bg-[#11151F]/80 border-t border-zinc-200/80 dark:border-zinc-800/80 text-[10px] font-mono text-zinc-400 dark:text-slate-500 text-center">
          ChromaDB Cosine Index • Grounded Context
        </div>
      </motion.aside>
    </AnimatePresence>
  );
};
