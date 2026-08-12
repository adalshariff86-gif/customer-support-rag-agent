import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  MessageSquare, 
  FileText, 
  Terminal, 
  Sparkles, 
  Search, 
  CheckCircle2, 
  Zap, 
  ExternalLink,
  ChevronRight,
  Sliders,
  Layers,
  Database
} from 'lucide-react';

export const InteractivePreview: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'sources' | 'developer'>('chat');
  const [typingStep, setTypingStep] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setTypingStep((prev) => (prev + 1) % 3);
    }, 4500);
    return () => clearInterval(timer);
  }, []);

  const sampleMessages = [
    {
      role: 'user',
      text: 'What is the refund policy?'
    },
    {
      role: 'assistant',
      text: 'Our refund policy allows you to request a refund within 30 days of purchase [Source 1].'
    }
  ];

  return (
    <div className="relative rounded-2xl overflow-hidden border border-zinc-200/80 dark:border-zinc-800/80 bg-white/90 dark:bg-[#0D1017]/90 shadow-2xl shadow-indigo-500/10 backdrop-blur-xl">
      {/* Window Title Bar */}
      <div className="px-4 py-3 bg-zinc-100/80 dark:bg-[#131722]/80 border-b border-zinc-200/80 dark:border-zinc-800/80 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-rose-500/80"></div>
          <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
          <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
          <span className="ml-2 font-mono text-xs text-zinc-500 dark:text-slate-400">
            resolvehq-preview.app
          </span>
        </div>

        {/* Tab switcher inside preview */}
        <div className="flex items-center bg-zinc-200/60 dark:bg-zinc-800/60 rounded-lg p-0.5 text-xs font-medium">
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-2.5 py-1 rounded-md transition-all ${
              activeTab === 'chat' 
                ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-slate-100 shadow-sm' 
                : 'text-zinc-500 dark:text-slate-400 hover:text-zinc-900 dark:hover:text-slate-200'
            }`}
          >
            Chat
          </button>
          <button
            onClick={() => setActiveTab('sources')}
            className={`px-2.5 py-1 rounded-md transition-all flex items-center gap-1 ${
              activeTab === 'sources' 
                ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-slate-100 shadow-sm' 
                : 'text-zinc-500 dark:text-slate-400 hover:text-zinc-900 dark:hover:text-slate-200'
            }`}
          >
            Sources <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
          </button>
          <button
            onClick={() => setActiveTab('developer')}
            className={`px-2.5 py-1 rounded-md transition-all flex items-center gap-1 ${
              activeTab === 'developer' 
                ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-slate-100 shadow-sm' 
                : 'text-zinc-500 dark:text-slate-400 hover:text-zinc-900 dark:hover:text-slate-200'
            }`}
          >
            Developer Mode
          </button>
        </div>
      </div>

      {/* Main Preview Workspace */}
      <div className="grid grid-cols-1 md:grid-cols-12 h-[380px]">
        {/* Mini Sidebar */}
        <div className="hidden md:block md:col-span-3 border-r border-zinc-200/80 dark:border-zinc-800/80 p-3 bg-zinc-50/50 dark:bg-[#0A0C10]/50 space-y-3 font-sans">
          <div className="flex items-center gap-2 px-2 py-1.5 rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium text-xs">
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Active Session</span>
          </div>

          <div className="space-y-1">
            <p className="text-[10px] font-mono uppercase text-zinc-400 dark:text-slate-500 px-2 font-semibold">
              Recent Queries
            </p>
            <div className="p-2 rounded-lg bg-zinc-100 dark:bg-zinc-800/50 text-xs text-zinc-800 dark:text-slate-200 font-medium truncate border border-zinc-200/50 dark:border-zinc-700/50">
              Refund Policy Request
            </div>
            <div className="p-2 rounded-lg hover:bg-zinc-100/50 dark:hover:bg-zinc-800/30 text-xs text-zinc-500 dark:text-slate-400 truncate cursor-pointer">
              Shipping Timeframes
            </div>
            <div className="p-2 rounded-lg hover:bg-zinc-100/50 dark:hover:bg-zinc-800/30 text-xs text-zinc-500 dark:text-slate-400 truncate cursor-pointer">
              Return Policy
            </div>
          </div>

          <div className="pt-8 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-emerald-600 dark:text-emerald-400 px-2">
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                ChromaDB
              </span>
              <span>181 Tests</span>
            </div>
          </div>
        </div>

        {/* Mini Workspace Content */}
        <div className="col-span-1 md:col-span-9 p-4 flex flex-col justify-between overflow-y-auto font-sans">
          {activeTab === 'chat' && (
            <div className="space-y-3">
              {/* User Message */}
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex justify-end"
              >
                <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-sm px-3.5 py-2 text-xs max-w-[85%] shadow-sm">
                  {sampleMessages[0].text}
                </div>
              </motion.div>

              {/* Assistant Message with RAG citation */}
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="flex justify-start items-start gap-2.5"
              >
                <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-[#5B5CEB] to-[#3B82F6] flex items-center justify-center text-white text-[10px] font-bold shrink-0 mt-1">
                  AI
                </div>
                <div className="bg-zinc-100 dark:bg-zinc-800/80 text-zinc-800 dark:text-slate-200 rounded-2xl rounded-tl-sm px-3.5 py-2.5 text-xs max-w-[90%] border border-zinc-200/60 dark:border-zinc-700/60 space-y-2">
                  <p className="leading-relaxed">
                    Our refund policy allows you to request a refund within 30 days of purchase
                    <button 
                      onClick={() => setActiveTab('sources')}
                      className="ml-1 text-indigo-600 dark:text-indigo-400 font-semibold underline underline-offset-2 hover:text-indigo-500"
                    >
                      [Source 1: Refund Policy]
                    </button>
                    .
                  </p>
                  
                  <div className="pt-2 border-t border-zinc-200/80 dark:border-zinc-700/80 flex items-center justify-between text-[10px] font-mono text-zinc-500 dark:text-slate-400">
                    <span className="flex items-center gap-1">
                      <Zap className="w-3 h-3 text-amber-500" /> Latency: 283ms
                    </span>
                    <button 
                      onClick={() => setActiveTab('developer')}
                      className="text-indigo-600 dark:text-indigo-400 hover:underline"
                    >
                      View Dev Metrics →
                    </button>
                  </div>
                </div>
              </motion.div>

              {/* Typing simulation prompt indicator */}
              <div className="pt-4">
                <div className="flex items-center gap-2 p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/60 text-xs text-zinc-400 dark:text-slate-500">
                  <Search className="w-3.5 h-3.5" />
                  <span className="font-mono text-[11px]">Query RAG engine (FastAPI + ChromaDB)...</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'sources' && (
            <motion.div 
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-3 text-xs"
            >
              <div className="flex items-center justify-between font-mono pb-2 border-b border-zinc-200 dark:border-zinc-800">
                <span className="font-semibold text-zinc-900 dark:text-slate-100 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-indigo-500" />
                  Retrieved Chunk #1 (Cosine Sim: 0.9845)
                </span>
                <span className="text-[10px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  Match Score: 98.45%
                </span>
              </div>

              <div className="p-3 rounded-xl bg-zinc-100/80 dark:bg-zinc-800/60 font-mono text-[11px] text-zinc-700 dark:text-slate-300 leading-relaxed border border-zinc-200/60 dark:border-zinc-700/60">
                "Our refund policy allows you to request a refund within 30 days of purchase. Please note that shipping costs are non-refundable."
              </div>

              <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                <div className="p-2 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
                  <span className="text-zinc-400 dark:text-slate-500">Document:</span>
                  <p className="font-medium text-zinc-800 dark:text-slate-200 truncate">refund_policy.md</p>
                </div>
                <div className="p-2 rounded-lg bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
                  <span className="text-zinc-400 dark:text-slate-500">Chunk ID:</span>
                  <p className="font-medium text-zinc-800 dark:text-slate-200 font-mono">chunk-sec-01</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'developer' && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="space-y-3 font-mono text-[11px]"
            >
              <div className="flex items-center justify-between pb-2 border-b border-zinc-200 dark:border-zinc-800">
                <span className="font-semibold text-zinc-900 dark:text-slate-100 flex items-center gap-1.5">
                  <Terminal className="w-4 h-4 text-emerald-500" />
                  RAG Pipeline Latency Breakdown
                </span>
                <span className="text-emerald-500 font-medium">Total: 283ms</span>
              </div>

              <div className="space-y-2">
                <div>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-zinc-500 dark:text-slate-400">Embedding (Sentence Transformers):</span>
                    <span className="text-zinc-800 dark:text-slate-200">42ms</span>
                  </div>
                  <div className="h-1.5 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                    <div className="h-full bg-blue-500 w-[15%]"></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-zinc-500 dark:text-slate-400">ChromaDB Vector Retrieval:</span>
                    <span className="text-zinc-800 dark:text-slate-200">31ms</span>
                  </div>
                  <div className="h-1.5 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 w-[11%]"></div>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-[10px] mb-1">
                    <span className="text-zinc-500 dark:text-slate-400">Gemini 3.5 LLM Generation:</span>
                    <span className="text-zinc-800 dark:text-slate-200">210ms</span>
                  </div>
                  <div className="h-1.5 w-full bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 w-[74%]"></div>
                  </div>
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-[#090D16] text-slate-300 border border-zinc-800 font-mono text-[10px] overflow-x-auto">
                <p className="text-indigo-400">// Prompt Tokens: 340 | Completion Tokens: 112 | Memory Turns: 1</p>
                <p className="text-emerald-400">// Top-K: 4 | Temp: 0.2 | Cosine Threshold: 0.65</p>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};
