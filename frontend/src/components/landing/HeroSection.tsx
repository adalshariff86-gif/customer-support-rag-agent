import React from 'react';
import { motion } from 'motion/react';
import { 
  ArrowRight, 
  Github, 
  Sparkles, 
  ShieldCheck, 
  Database, 
  Cpu, 
  Zap,
  Activity
} from 'lucide-react';
import { useStore } from '../../store/useStore';
import { InteractivePreview } from './InteractivePreview';

export const HeroSection: React.FC = () => {
  const { setActiveTab } = useStore();

  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden">
      {/* Subtle Background Glow Accent (No tacky huge blobs or neon cyberpunk slop) */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-indigo-500/10 dark:bg-indigo-600/10 blur-[120px] rounded-full pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          
          {/* Left Column: Copy & Actions */}
          <div className="lg:col-span-6 space-y-6 text-left">
            {/* Pill Tag */}
            <motion.div 
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-zinc-100 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700/60 text-xs font-mono font-medium text-zinc-700 dark:text-slate-300"
            >
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>FastAPI + ChromaDB + Gemini 3.5</span>
              <span className="text-zinc-400 dark:text-slate-500">•</span>
              <span className="text-indigo-600 dark:text-indigo-400 font-semibold">181 Tests Passing</span>
            </motion.div>

            {/* Main Headline */}
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-zinc-900 dark:text-slate-100 leading-[1.08]"
            >
              Every Customer Question.<br />
              <span className="bg-gradient-to-r from-[#5B5CEB] via-[#3B82F6] to-[#60A5FA] bg-clip-text text-transparent">
                Resolved with Context.
              </span>
            </motion.h1>

            {/* Subtitle */}
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-base sm:text-lg text-zinc-600 dark:text-slate-300 max-w-xl leading-relaxed font-sans"
            >
              ResolveHQ is the autonomous support intelligence platform powered by Retrieval-Augmented Generation (RAG), ChromaDB vector embeddings, and Gemini 3.5.
            </motion.p>

            {/* Action Buttons */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-wrap items-center gap-4 pt-2"
            >
              <button
                onClick={() => setActiveTab('app')}
                className="flex items-center gap-2.5 px-6 py-3.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-[#5B5CEB] to-[#3B82F6] dark:from-[#7C6CFF] dark:to-[#60A5FA] shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
              >
                <span>Launch App</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <a
                href="https://github.com/adalshariff86-gif/customer-support-rag-agent"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 px-5 py-3.5 rounded-xl text-sm font-medium text-zinc-700 dark:text-slate-300 bg-zinc-100 dark:bg-zinc-800/80 hover:bg-zinc-200/80 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-700/60 transition-all duration-200"
              >
                <Github className="w-4 h-4" />
                <span>GitHub Repository</span>
              </a>
            </motion.div>

            {/* Key Tech Specs Row */}
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.4 }}
              className="pt-6 border-t border-zinc-200/80 dark:border-zinc-800/80 grid grid-cols-3 gap-4 text-xs font-mono"
            >
              <div>
                <span className="block text-zinc-400 dark:text-slate-500 font-semibold uppercase text-[10px]">Vector DB</span>
                <span className="font-semibold text-zinc-800 dark:text-slate-200">ChromaDB Store</span>
              </div>
              <div>
                <span className="block text-zinc-400 dark:text-slate-500 font-semibold uppercase text-[10px]">AI Model</span>
                <span className="font-semibold text-zinc-800 dark:text-slate-200">Gemini 3.5 Flash</span>
              </div>
              <div>
                <span className="block text-zinc-400 dark:text-slate-500 font-semibold uppercase text-[10px]">Embeddings</span>
                <span className="font-semibold text-zinc-800 dark:text-slate-200">MiniLM-L6-v2</span>
              </div>
            </motion.div>
          </div>

          {/* Right Column: Real Product Preview */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:col-span-6"
            id="preview"
          >
            <InteractivePreview />
          </motion.div>

        </div>
      </div>
    </section>
  );
};
