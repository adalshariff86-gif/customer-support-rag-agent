import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { 
  Sparkles, 
  Terminal, 
  BookOpen, 
  Github, 
  Sun, 
  Moon, 
  ArrowRight,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import { useStore } from '../../store/useStore';

export const Navbar: React.FC = () => {
  const { activeTab, setActiveTab, theme, setTheme } = useStore();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleTheme = () => {
    if (theme === 'dark') setTheme('light');
    else setTheme('dark');
  };

  return (
    <header 
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled 
          ? 'bg-white/80 dark:bg-[#0A0C10]/80 backdrop-blur-md border-b border-zinc-200/80 dark:border-zinc-800/80 shadow-sm py-3' 
          : 'bg-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Brand Logo */}
        <div 
          onClick={() => setActiveTab('landing')}
          className="flex items-center gap-2.5 cursor-pointer group"
        >
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-[#5B5CEB] to-[#3B82F6] dark:from-[#7C6CFF] dark:to-[#60A5FA] flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:scale-105 transition-transform duration-200">
            <Cpu className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-lg tracking-tight text-zinc-900 dark:text-slate-100 flex items-center gap-1.5">
              ResolveHQ
              <span className="px-1.5 py-0.5 text-[10px] font-mono font-medium rounded-full bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800/50">
                v3.5
              </span>
            </span>
            <span className="text-[10px] text-zinc-500 dark:text-zinc-400 font-medium hidden sm:inline-block -mt-0.5">
              Every Question. Resolved with Context.
            </span>
          </div>
        </div>

        {/* Center Nav Links */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-600 dark:text-slate-400">
          <a 
            href="#preview" 
            className="hover:text-zinc-900 dark:hover:text-slate-100 transition-colors"
          >
            Product
          </a>
          <a 
            href="#how-it-works" 
            className="hover:text-zinc-900 dark:hover:text-slate-100 transition-colors"
          >
            Architecture
          </a>
          <a 
            href="#tech-stack" 
            className="hover:text-zinc-900 dark:hover:text-slate-100 transition-colors"
          >
            Tech Stack
          </a>
          <a 
            href="#developer-features" 
            className="hover:text-zinc-900 dark:hover:text-slate-100 transition-colors flex items-center gap-1"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            181 Tests
          </a>
          <a 
            href="https://github.com/adalshariff86-gif/customer-support-rag-agent" 
            target="_blank" 
            rel="noreferrer"
            className="hover:text-zinc-900 dark:hover:text-slate-100 transition-colors flex items-center gap-1"
          >
            <Github className="w-4 h-4" />
            GitHub
          </a>
        </nav>

        {/* Actions & CTA */}
        <div className="flex items-center gap-3">
          {/* Theme Switcher */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg text-zinc-600 dark:text-slate-400 hover:bg-zinc-100 dark:hover:bg-zinc-800/60 transition-colors"
            title="Toggle Theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-400" />
            ) : (
              <Moon className="w-4 h-4 text-zinc-700" />
            )}
          </button>

          {/* Launch App Button */}
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setActiveTab('app')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-[#5B5CEB] to-[#3B82F6] dark:from-[#7C6CFF] dark:to-[#60A5FA] shadow-md shadow-indigo-500/20 hover:shadow-indigo-500/35 transition-all duration-200"
          >
            <span>{activeTab === 'app' ? 'Back to Overview' : 'Launch App'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </motion.button>
        </div>
      </div>
    </header>
  );
};
