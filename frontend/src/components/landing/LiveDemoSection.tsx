import React, { useState } from 'react';
import { motion } from 'motion/react';
import { 
  Send, 
  Sparkles, 
  Zap, 
  Terminal, 
  FileText, 
  ShieldCheck, 
  ArrowRight,
  Cpu,
  RefreshCw
} from 'lucide-react';
import { useStore } from '../../store/useStore';
import { apiService } from '../../services/api';

export const LiveDemoSection: React.FC = () => {
  const { setActiveTab } = useStore();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<any>(null);

  const sampleQueries = [
    'How do I verify webhook HMAC signatures?',
    'What are the rate limits for Enterprise plans?',
    'What is the refund policy for annual subscriptions?',
    'How does ResolveHQ support OAuth PKCE SSO?'
  ];

  const handleRunDemo = async (textToRun: string) => {
    if (!textToRun.trim() || loading) return;
    setQuery(textToRun);
    setLoading(true);
    setResponse(null);

    try {
      const data = await apiService.postChat(textToRun);
      const metrics = {
        total_latency_ms: data.latency_ms || 0,
        model: data.model || 'gemini'
      };
      setResponse({ ...data, metrics });
    } catch (err) {
      console.error('Demo execution error:', err);
      setResponse({
        answer: 'Failed to connect to backend server. Please verify backend state.',
        error: true
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <section id="live-demo" className="py-24 bg-white dark:bg-[#0A0C10] transition-colors border-t border-zinc-200/80 dark:border-zinc-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
            <Zap className="w-3.5 h-3.5" />
            <span>Interactive Backend Sandbox</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-slate-100">
            Test Live RAG Retrieval Right Now
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 dark:text-slate-400">
            Sends real requests directly to <code className="font-mono bg-zinc-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded text-indigo-600 dark:text-indigo-400">POST /chat</code>. Grounded in live ChromaDB vector indexes.
          </p>
        </div>

        {/* Demo Interactive Box */}
        <div className="max-w-4xl mx-auto rounded-2xl bg-zinc-50 dark:bg-[#0F131C] border border-zinc-200/80 dark:border-zinc-800/80 p-6 shadow-xl space-y-6">
          
          {/* Sample Prompts Row */}
          <div className="space-y-2">
            <span className="text-xs font-mono uppercase text-zinc-400 dark:text-slate-500 font-semibold block">
              Sample Production Queries:
            </span>
            <div className="flex flex-wrap gap-2">
              {sampleQueries.map((q) => (
                <button
                  key={q}
                  onClick={() => handleRunDemo(q)}
                  disabled={loading}
                  className="px-3 py-1.5 rounded-lg bg-white dark:bg-zinc-800/80 border border-zinc-200/80 dark:border-zinc-700/60 text-xs text-zinc-700 dark:text-slate-300 hover:border-indigo-500/80 hover:text-indigo-600 dark:hover:text-indigo-400 transition-all text-left font-sans shadow-sm"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Input Form */}
          <form 
            onSubmit={(e) => {
              e.preventDefault();
              handleRunDemo(query);
            }} 
            className="flex items-center gap-3"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Type a support query to test RAG retrieval..."
              className="flex-1 px-4 py-3 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-sm text-zinc-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-5 py-3 rounded-xl bg-gradient-to-r from-[#5B5CEB] to-[#3B82F6] text-white text-xs font-semibold flex items-center gap-2 shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Querying RAG...
                </>
              ) : (
                <>
                  <span>Send</span> <Send className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Response Output Box */}
          {response && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 rounded-xl bg-white dark:bg-zinc-900/90 border border-zinc-200 dark:border-zinc-800 space-y-4 text-xs font-sans"
            >
              <div className="flex items-center justify-between pb-3 border-b border-zinc-200 dark:border-zinc-800">
                <span className="font-semibold text-zinc-900 dark:text-slate-100 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-500" />
                  Grounded Response
                </span>
                {response.metrics && (
                  <span className="font-mono text-[11px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 font-medium">
                    Total Latency: {response.metrics.total_latency_ms}ms
                  </span>
                )}
              </div>

              <div className="prose dark:prose-invert max-w-none text-zinc-800 dark:text-slate-200 leading-relaxed font-sans text-xs whitespace-pre-wrap">
                {response.answer}
              </div>

              {/* Citations list */}
              {response.sources && response.sources.length > 0 && (
                <div className="pt-3 border-t border-zinc-200 dark:border-zinc-800 space-y-2">
                  <span className="font-mono text-[11px] text-zinc-400 dark:text-slate-500 font-semibold block">
                    Cited Knowledge Base Documents ({response.sources.length}):
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {response.sources.map((src: any, idx: number) => (
                      <div key={idx} className="p-2.5 rounded-lg bg-zinc-50 dark:bg-zinc-800/60 border border-zinc-200/80 dark:border-zinc-700/60 text-[11px] font-mono">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-zinc-800 dark:text-slate-200 truncate">
                            [Source {idx + 1}] {src.metadata?.source || src.id}
                          </span>
                          <span className="text-emerald-500 font-semibold">
                            {((src.score ?? 0) * 100).toFixed(1)}%
                          </span>
                        </div>
                        <p className="text-zinc-500 dark:text-slate-400 line-clamp-1 mt-0.5 font-sans text-[10px]">
                          {src.content}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}

          {/* Launch Full Workspace CTA */}
          <div className="pt-2 flex items-center justify-between text-xs font-mono text-zinc-500 dark:text-slate-400">
            <span>Want full chat history, settings, and developer drawers?</span>
            <button
              onClick={() => setActiveTab('app')}
              className="text-indigo-600 dark:text-indigo-400 font-semibold flex items-center gap-1 hover:underline"
            >
              Open Full Dashboard Workspace →
            </button>
          </div>

        </div>
      </div>
    </section>
  );
};
