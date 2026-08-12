import React from 'react';
import { Cpu, Github, ExternalLink, ShieldCheck, Terminal, Heart } from 'lucide-react';
import { useStore } from '../../store/useStore';

export const Footer: React.FC = () => {
  const { setActiveTab } = useStore();

  return (
    <footer className="bg-zinc-50 dark:bg-[#07090D] border-t border-zinc-200 dark:border-zinc-800/80 pt-16 pb-12 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-10 mb-12">
          {/* Column 1: Brand Info */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-[#5B5CEB] to-[#3B82F6] dark:from-[#7C6CFF] dark:to-[#60A5FA] flex items-center justify-center text-white shadow-sm">
                <Cpu className="w-4 h-4" />
              </div>
              <span className="font-semibold text-base text-zinc-900 dark:text-slate-100">
                ResolveHQ
              </span>
            </div>
            <p className="text-sm text-zinc-600 dark:text-slate-400 max-w-sm leading-relaxed">
              Every Customer Question. Resolved with Context. Enterprise support intelligence platform driven by RAG, ChromaDB vector retrieval, and Gemini AI.
            </p>
            <div className="flex items-center gap-2 pt-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                181 Passing Backend Tests
              </span>
            </div>
          </div>

          {/* Column 2: Product */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 dark:text-slate-500 font-mono">
              Product
            </h4>
            <ul className="space-y-2 text-sm text-zinc-600 dark:text-slate-400">
              <li>
                <button onClick={() => setActiveTab('app')} className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Launch Platform
                </button>
              </li>
              <li>
                <a href="#preview" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  RAG Interface
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Interactive Pipeline
                </a>
              </li>
              <li>
                <a href="#tech-stack" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Architecture Stack
                </a>
              </li>
            </ul>
          </div>

          {/* Column 3: Developers */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 dark:text-slate-500 font-mono">
              Developers
            </h4>
            <ul className="space-y-2 text-sm text-zinc-600 dark:text-slate-400">
              <li>
                <a href="http://127.0.0.1:8000/chat/health" target="_blank" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors flex items-center gap-1">
                  API Health Status <ExternalLink className="w-3 h-3 opacity-60" />
                </a>
              </li>
              <li>
                <a href="http://127.0.0.1:8000/documents" target="_blank" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors flex items-center gap-1">
                  Vector Documents API <ExternalLink className="w-3 h-3 opacity-60" />
                </a>
              </li>
              <li>
                <a href="#developer-features" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  FastAPI Dependency Injection
                </a>
              </li>
              <li>
                <a href="https://github.com/adalshariff86-gif/customer-support-rag-agent" target="_blank" rel="noreferrer" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors flex items-center gap-1">
                  GitHub Repository <Github className="w-3 h-3 opacity-60" />
                </a>
              </li>
            </ul>
          </div>

          {/* Column 4: Contact & Social */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 dark:text-slate-500 font-mono">
              Connect
            </h4>
            <ul className="space-y-2 text-sm text-zinc-600 dark:text-slate-400">
              <li>
                <a href="https://linkedin.com" target="_blank" rel="noreferrer" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  LinkedIn
                </a>
              </li>
              <li>
                <a href="https://github.com/adalshariff86-gif" target="_blank" rel="noreferrer" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  GitHub Profile
                </a>
              </li>
              <li>
                <a href="mailto:support@resolvehq.io" className="hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">
                  Developer Contact
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-zinc-200/80 dark:border-zinc-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-zinc-500 dark:text-slate-500 gap-4 font-mono">
          <div>
            © 2026 ResolveHQ. All rights reserved. Built for high-scale enterprise support.
          </div>
          <div className="flex items-center gap-4">
            <span>FastAPI + ChromaDB + Gemini 3.5</span>
            <span>•</span>
            <span>181/181 Passing Tests</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
