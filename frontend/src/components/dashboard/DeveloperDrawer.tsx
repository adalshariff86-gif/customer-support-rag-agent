import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  X, 
  Terminal, 
  Cpu, 
  Database, 
  Sparkles, 
  Zap, 
  BarChart3, 
  Layers, 
  Copy, 
  Check,
  Code
} from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { useStore } from '../../store/useStore';

export const DeveloperDrawer: React.FC = () => {
  const { 
    isDeveloperDrawerOpen, 
    setDeveloperDrawerOpen, 
    messages 
  } = useStore();

  const [copiedJson, setCopiedJson] = React.useState(false);

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isDeveloperDrawerOpen) {
        setDeveloperDrawerOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isDeveloperDrawerOpen, setDeveloperDrawerOpen]);

  const lastAssistantMessage = [...messages].reverse().find((m) => m.role === 'assistant');
  const metrics = lastAssistantMessage?.metrics;

  if (!isDeveloperDrawerOpen || !metrics) return null;

  // Chart data for similarity scores
  const similarityChartData = metrics.similarity_scores.map((score, idx) => ({
    name: `Chunk #${idx + 1}`,
    score: parseFloat((score * 100).toFixed(1))
  }));

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(metrics, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ y: 350, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 350, opacity: 0 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed bottom-0 left-0 right-0 z-40 bg-zinc-900/95 dark:bg-[#080B10]/95 backdrop-blur-xl border-t border-zinc-700/80 dark:border-zinc-800 text-slate-100 font-mono shadow-2xl overflow-hidden"
      >
        {/* Drawer Header */}
        <div className="px-6 py-3 bg-zinc-950/80 border-b border-zinc-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-400">
              <Terminal className="w-4 h-4" />
              <span>Developer Telemetry & RAG Metrics</span>
            </div>
            <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/20">
              SLA Latency: {metrics.total_latency_ms}ms
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyJson}
              className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-xs text-slate-300 flex items-center gap-1 transition-colors"
            >
              {copiedJson ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
              <span>{copiedJson ? 'Copied' : 'Copy Payload JSON'}</span>
            </button>
            <button
              onClick={() => setDeveloperDrawerOpen(false)}
              className="p-1 rounded text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Drawer Main Body */}
        <div className="p-6 max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-6 text-xs max-h-[300px] overflow-y-auto">
          
          {/* Column 1: Latency Breakdown */}
          <div className="md:col-span-4 space-y-3 bg-zinc-950/60 p-4 rounded-xl border border-zinc-800">
            <h4 className="text-[11px] uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-amber-400" /> Latency Breakdown ({metrics.total_latency_ms}ms)
            </h4>

            <div className="space-y-2.5 pt-1">
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-400">1. Embedding (Sentence Transformers):</span>
                  <span className="text-blue-400 font-bold">{metrics.embedding_time_ms}ms</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${Math.max(8, (metrics.embedding_time_ms / metrics.total_latency_ms) * 100)}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-400">2. Vector Search (ChromaDB Cosine):</span>
                  <span className="text-emerald-400 font-bold">{metrics.retrieval_time_ms}ms</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full"
                    style={{ width: `${Math.max(8, (metrics.retrieval_time_ms / metrics.total_latency_ms) * 100)}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span className="text-slate-400">3. LLM Synthesis (Gemini 3.5):</span>
                  <span className="text-indigo-400 font-bold">{metrics.llm_time_ms}ms</span>
                </div>
                <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 rounded-full"
                    style={{ width: `${Math.max(8, (metrics.llm_time_ms / metrics.total_latency_ms) * 100)}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Column 2: Vector Similarity Scores Chart */}
          <div className="md:col-span-4 bg-zinc-950/60 p-4 rounded-xl border border-zinc-800 space-y-2">
            <h4 className="text-[11px] uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1.5">
              <BarChart3 className="w-3.5 h-3.5 text-indigo-400" /> Top-K Similarity Distribution (%)
            </h4>
            <div className="h-36 pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={similarityChartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <XAxis dataKey="name" tick={{ fill: '#94A3B8', fontSize: 10 }} />
                  <YAxis domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 10 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0F172A', borderColor: '#334155', borderRadius: '8px', fontSize: '11px' }} 
                  />
                  <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                    {similarityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={index === 0 ? '#10B981' : '#6366F1'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Column 3: Token Usage & Memory State */}
          <div className="md:col-span-4 bg-zinc-950/60 p-4 rounded-xl border border-zinc-800 space-y-3">
            <h4 className="text-[11px] uppercase tracking-wider text-slate-400 font-bold flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-purple-400" /> Token & Model Telemetry
            </h4>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-slate-400 block text-[10px]">Memory Buffer Turns:</span>
                <span className="font-bold text-emerald-400">{metrics.memory_turns_count}</span>
              </div>
              <div className="p-2 rounded bg-zinc-900 border border-zinc-800">
                <span className="text-slate-400 block text-[10px]">Model:</span>
                <span className="font-bold text-indigo-400">{metrics.model || 'Gemini 3.5 Flash'}</span>
              </div>
            </div>

            <div className="pt-1 text-[10px] text-slate-400 flex items-center justify-between border-t border-zinc-800">
              <span>Provider: {metrics.provider}</span>
              <span>Model: {metrics.model}</span>
            </div>
          </div>

        </div>
      </motion.div>
    </AnimatePresence>
  );
};
