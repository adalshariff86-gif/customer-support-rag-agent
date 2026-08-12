import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  MessageSquare, 
  Cpu, 
  Database, 
  Layers, 
  Sparkles, 
  CheckCircle2, 
  Play, 
  Pause, 
  RotateCcw,
  ArrowRight,
  Code
} from 'lucide-react';

interface PipelineStep {
  id: number;
  title: string;
  subtitle: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  timing: string;
  codeSnippet: string;
  color: string;
}

const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: 1,
    title: 'User Asks Question',
    subtitle: 'HTTP POST /chat Request Payload',
    description: 'The user submits an inquiry via support widget. The system captures conversation session context and user query.',
    icon: MessageSquare,
    timing: '0ms',
    codeSnippet: '{\n  "message": "What is the refund policy?",\n  "conversation_id": "conv_9812"\n}',
    color: 'from-blue-500 to-indigo-600'
  },
  {
    id: 2,
    title: 'Embedding Created',
    subtitle: 'Sentence Transformers (384 Dimensions)',
    description: 'The query text is passed through sentence-transformers/all-MiniLM-L6-v2 to generate dense 384-dimensional vector embeddings.',
    icon: Cpu,
    timing: '42ms',
    codeSnippet: 'vector = model.encode(user_message) # shape: (384,)',
    color: 'from-indigo-500 to-purple-600'
  },
  {
    id: 3,
    title: 'ChromaDB Retrieves',
    subtitle: 'Vector Cosine Distance Search',
    description: 'ChromaDB performs nearest neighbor vector search against indexed enterprise knowledge base collections.',
    icon: Database,
    timing: '31ms',
    codeSnippet: 'results = collection.query(\n  query_embeddings=[vector],\n  n_results=top_k\n)',
    color: 'from-emerald-500 to-teal-600'
  },
  {
    id: 4,
    title: 'Top Documents Selected',
    subtitle: 'Top-K Filtering & Score Verification',
    description: 'The top k chunks are score-filtered (threshold > 0.65) and formatted into structured citation blocks.',
    icon: Layers,
    timing: '5ms',
    codeSnippet: 'sources = [chunk for chunk in results if chunk.score >= 0.65]',
    color: 'from-amber-500 to-orange-600'
  },
  {
    id: 5,
    title: 'Gemini Generates Response',
    subtitle: 'Grounded Prompt Synthesis',
    description: 'Gemini 3.5 Flash processes the system prompt, conversation memory buffer, and retrieved citations to form a response.',
    icon: Sparkles,
    timing: '210ms',
    codeSnippet: 'response = ai.models.generate_content(\n  model="gemini-3.5-flash",\n  contents=[grounded_prompt]\n)',
    color: 'from-violet-500 to-pink-600'
  },
  {
    id: 6,
    title: 'Answer Returned',
    subtitle: 'Streaming Output with Citations',
    description: 'The assistant streams grounded response with inline citation chips [Source 1], source metadata, and dev metrics.',
    icon: CheckCircle2,
    timing: '283ms total',
    codeSnippet: 'return {\n  "answer": "...",\n  "sources": [...],\n  "metrics": {...}\n}',
    color: 'from-indigo-600 to-blue-600'
  }
];

export const HowItWorks: React.FC = () => {
  const [activeStep, setActiveStep] = useState(1);
  const [isPlaying, setIsPlaying] = useState(true);

  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev >= 6 ? 1 : prev + 1));
    }, 3200);
    return () => clearInterval(interval);
  }, [isPlaying]);

  return (
    <section id="how-it-works" className="py-24 bg-zinc-50/50 dark:bg-[#080A0E] border-y border-zinc-200/80 dark:border-zinc-800/80 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
            <Cpu className="w-3.5 h-3.5" />
            <span>Retrieval-Augmented Generation Architecture</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-slate-100">
            How ResolveHQ Works
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 dark:text-slate-400">
            Every customer support query travels through our 6-stage grounded RAG execution pipeline in under 300ms.
          </p>

          {/* Timeline Controls */}
          <div className="pt-2 flex items-center justify-center gap-3">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-200 dark:bg-zinc-800 text-xs font-mono font-medium text-zinc-700 dark:text-slate-300 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
            >
              {isPlaying ? (
                <>
                  <Pause className="w-3.5 h-3.5" /> Pause Auto-Cycle
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" /> Auto-Play Timeline
                </>
              )}
            </button>
            <button
              onClick={() => setActiveStep(1)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-200 dark:bg-zinc-800 text-xs font-mono font-medium text-zinc-700 dark:text-slate-300 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Reset
            </button>
          </div>
        </div>

        {/* Interactive Timeline Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          
          {/* Node Selector Steps (Left Column) */}
          <div className="lg:col-span-6 space-y-3">
            {PIPELINE_STEPS.map((step) => {
              const Icon = step.icon;
              const isActive = activeStep === step.id;

              return (
                <div
                  key={step.id}
                  onClick={() => {
                    setActiveStep(step.id);
                    setIsPlaying(false);
                  }}
                  className={`relative cursor-pointer p-4 rounded-xl border transition-all duration-300 ${
                    isActive
                      ? 'bg-white dark:bg-[#11151F] border-indigo-500/80 dark:border-indigo-500/80 shadow-lg shadow-indigo-500/10 scale-[1.01]'
                      : 'bg-white/60 dark:bg-[#0D1017]/60 border-zinc-200/80 dark:border-zinc-800/80 hover:bg-white dark:hover:bg-[#11151F]'
                  }`}
                >
                  <div className="flex items-start gap-4">
                    {/* Node Number / Icon */}
                    <div
                      className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 transition-all duration-300 ${
                        isActive
                          ? `bg-gradient-to-tr ${step.color} text-white shadow-md`
                          : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-slate-400'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className={`text-sm font-semibold tracking-tight ${isActive ? 'text-zinc-900 dark:text-slate-100' : 'text-zinc-700 dark:text-slate-300'}`}>
                          {step.id}. {step.title}
                        </h3>
                        <span className="font-mono text-[11px] text-zinc-500 dark:text-slate-400 bg-zinc-100 dark:bg-zinc-800/80 px-2 py-0.5 rounded">
                          {step.timing}
                        </span>
                      </div>
                      <p className="text-xs text-zinc-500 dark:text-slate-400 mt-1 line-clamp-1 font-sans">
                        {step.subtitle}
                      </p>
                    </div>
                  </div>

                  {/* Active particle traveler bar */}
                  {isActive && (
                    <motion.div
                      layoutId="activeTimelineBar"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-blue-500 rounded-b-xl"
                    />
                  )}
                </div>
              );
            })}
          </div>

          {/* Active Step Payload Inspector (Right Column) */}
          <div className="lg:col-span-6">
            <AnimatePresence mode="wait">
              {PIPELINE_STEPS.filter((s) => s.id === activeStep).map((step) => {
                const Icon = step.icon;
                return (
                  <motion.div
                    key={step.id}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -15 }}
                    transition={{ duration: 0.3 }}
                    className="p-6 rounded-2xl bg-white dark:bg-[#0F131C] border border-zinc-200/80 dark:border-zinc-800/80 shadow-xl space-y-5"
                  >
                    <div className="flex items-center justify-between pb-4 border-b border-zinc-200 dark:border-zinc-800">
                      <div className="flex items-center gap-3">
                        <div className={`p-2.5 rounded-xl bg-gradient-to-tr ${step.color} text-white shadow-sm`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div>
                          <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-600 dark:text-indigo-400 font-bold">
                            Stage {step.id} of 6
                          </span>
                          <h4 className="text-lg font-bold text-zinc-900 dark:text-slate-100">
                            {step.title}
                          </h4>
                        </div>
                      </div>
                      <span className="font-mono text-xs px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20 font-semibold">
                        Latency: {step.timing}
                      </span>
                    </div>

                    <p className="text-xs sm:text-sm text-zinc-600 dark:text-slate-300 leading-relaxed font-sans">
                      {step.description}
                    </p>

                    {/* Execution Code Snippet */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-[11px] font-mono text-zinc-400 dark:text-slate-500">
                        <span className="flex items-center gap-1">
                          <Code className="w-3.5 h-3.5" /> Backend Implementation
                        </span>
                        <span>Python / FastAPI</span>
                      </div>
                      <pre className="p-4 rounded-xl bg-[#090D16] text-slate-200 font-mono text-xs overflow-x-auto border border-zinc-800 leading-relaxed">
                        <code>{step.codeSnippet}</code>
                      </pre>
                    </div>

                    <div className="pt-2 flex items-center justify-between text-xs text-zinc-500 dark:text-slate-400 font-mono">
                      <span>Step {step.id}/6 Completed</span>
                      <button
                        onClick={() => setActiveStep((prev) => (prev >= 6 ? 1 : prev + 1))}
                        className="text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 font-semibold"
                      >
                        Next Stage <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>

        </div>
      </div>
    </section>
  );
};
