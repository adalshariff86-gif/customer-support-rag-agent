import React from 'react';
import { motion } from 'motion/react';
import { 
  Zap, 
  Sparkles, 
  Database, 
  Cpu, 
  Layout, 
  Palette, 
  Activity,
  Code
} from 'lucide-react';

interface TechItem {
  name: string;
  role: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  tag: string;
  gradient: string;
}

const TECH_STACK_ITEMS: TechItem[] = [
  {
    name: 'FastAPI',
    role: 'Asynchronous Python Backend',
    description: 'High-performance API framework with automated Pydantic validation, OpenAPI specs, and async concurrency.',
    icon: Zap,
    tag: 'Backend Core',
    gradient: 'from-emerald-500 to-teal-600'
  },
  {
    name: 'Gemini 3.5 Flash',
    role: 'Grounded LLM Generation',
    description: 'Google DeepMind flagship language model providing ultra-fast grounded responses with strict context constraints.',
    icon: Sparkles,
    tag: 'Generative AI',
    gradient: 'from-indigo-500 to-blue-600'
  },
  {
    name: 'OpenRouter',
    role: 'Unified AI Provider Gateway',
    description: 'Multi-model routing layer enabling seamless fallback between Gemini and other LLM providers with unified API access.',
    icon: Zap,
    tag: 'AI Gateway',
    gradient: 'from-cyan-500 to-blue-600'
  },
  {
    name: 'ChromaDB',
    role: 'Open-Source Vector Database',
    description: 'High-speed vector database engineered for similarity search, cosine metadata filtering, and persistent document storage.',
    icon: Database,
    tag: 'Vector Storage',
    gradient: 'from-purple-500 to-indigo-600'
  },
  {
    name: 'Sentence Transformers',
    role: 'all-MiniLM-L6-v2 Embeddings',
    description: 'Generates 384-dimensional dense semantic vector representations for enterprise support document chunks.',
    icon: Cpu,
    tag: 'Embeddings Engine',
    gradient: 'from-amber-500 to-orange-600'
  },
  {
    name: 'React 19 & TypeScript',
    role: 'Modern Frontend Architecture',
    description: 'Type-safe React client application with state management, custom hooks, and zero client key exposures.',
    icon: Layout,
    tag: 'Frontend SPA',
    gradient: 'from-blue-500 to-cyan-600'
  },
  {
    name: 'TailwindCSS & Motion',
    role: 'Enterprise Design & Motion',
    description: 'Utility-first styling with 60 FPS Framer Motion transitions, responsive layouts, and WCAG AA accessibility.',
    icon: Palette,
    tag: 'Design System',
    gradient: 'from-violet-500 to-purple-600'
  }
];

export const TechStack: React.FC = () => {
  return (
    <section id="tech-stack" className="py-24 bg-white dark:bg-[#0A0C10] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Title */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
            <Code className="w-3.5 h-3.5" />
            <span>Modern Production Stack</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-zinc-900 dark:text-slate-100">
            Engineered with Industry Standard Infrastructure
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 dark:text-slate-400">
            Built on robust, asynchronous, enterprise-ready frameworks designed for scale and developer productivity.
          </p>
        </div>

        {/* Tech Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {TECH_STACK_ITEMS.map((item, index) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.08 }}
                whileHover={{ y: -4 }}
                className="p-6 rounded-2xl bg-zinc-50/80 dark:bg-[#0F131C] border border-zinc-200/80 dark:border-zinc-800/80 hover:border-zinc-300 dark:hover:border-zinc-700 shadow-sm hover:shadow-md transition-all duration-300 space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className={`p-3 rounded-xl bg-gradient-to-tr ${item.gradient} text-white shadow-sm`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className="text-[10px] font-mono font-semibold px-2.5 py-1 rounded-full bg-zinc-200/60 dark:bg-zinc-800 text-zinc-700 dark:text-slate-300">
                      {item.tag}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-zinc-900 dark:text-slate-100 tracking-tight">
                      {item.name}
                    </h3>
                    <p className="text-xs font-mono text-indigo-600 dark:text-indigo-400 font-medium">
                      {item.role}
                    </p>
                  </div>

                  <p className="text-xs sm:text-sm text-zinc-600 dark:text-slate-400 leading-relaxed font-sans">
                    {item.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-zinc-200/60 dark:border-zinc-800/60 flex items-center justify-between text-[11px] font-mono text-zinc-400 dark:text-slate-500">
                  <span>Verified Architecture</span>
                  <span className="text-emerald-500">Active</span>
                </div>
              </motion.div>
            );
          })}
        </div>

      </div>
    </section>
  );
};
