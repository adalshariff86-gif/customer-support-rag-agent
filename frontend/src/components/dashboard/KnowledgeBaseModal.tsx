import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Database, Plus, FileText, CheckCircle2, ShieldCheck, Upload, Sparkles } from 'lucide-react';
import { useStore } from '../../store/useStore';

export const KnowledgeBaseModal: React.FC = () => {
  const { 
    isKnowledgeBaseOpen, 
    setKnowledgeBaseOpen, 
    documents, 
    fetchDocuments, 
    addDocument 
  } = useStore();

  const [activeTab, setActiveTab] = useState<'docs' | 'upload'>('docs');
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState<'API' | 'Policy' | 'Billing' | 'Security' | 'Integration'>('API');
  const [newContent, setNewContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (isKnowledgeBaseOpen) {
      fetchDocuments();
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isKnowledgeBaseOpen) {
        setKnowledgeBaseOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isKnowledgeBaseOpen, fetchDocuments, setKnowledgeBaseOpen]);

  const handleUploadDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setSuccessMessage('');

    const ok = await addDocument(newTitle, newContent, newCategory);
    setIsSubmitting(false);

    if (ok) {
      setSuccessMessage(`Document "${newTitle}" successfully indexed into ChromaDB vector store!`);
      setNewTitle('');
      setNewContent('');
      setTimeout(() => {
        setSuccessMessage('');
        setActiveTab('docs');
      }, 1500);
    }
  };

  if (!isKnowledgeBaseOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="w-full max-w-2xl rounded-2xl bg-white dark:bg-[#0F131C] border border-zinc-200/80 dark:border-zinc-800/80 shadow-2xl overflow-hidden font-sans text-zinc-900 dark:text-slate-100"
        >
          {/* Header */}
          <div className="px-6 py-4 bg-zinc-50 dark:bg-[#131722] border-b border-zinc-200/80 dark:border-zinc-800/80 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-purple-500" />
              <div>
                <h3 className="font-bold text-sm">ChromaDB Vector Knowledge Store</h3>
                <p className="text-[10px] font-mono text-zinc-400 dark:text-slate-500">
                  Sentence Transformers Vector Index
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="flex bg-zinc-200/80 dark:bg-zinc-800 p-0.5 rounded-lg text-xs font-mono">
                <button
                  onClick={() => setActiveTab('docs')}
                  className={`px-3 py-1 rounded-md transition-all ${
                    activeTab === 'docs' ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-slate-100 shadow-xs' : 'text-zinc-500'
                  }`}
                >
                  Indexed Docs
                </button>
                <button
                  onClick={() => setActiveTab('upload')}
                  className={`px-3 py-1 rounded-md transition-all flex items-center gap-1 ${
                    activeTab === 'upload' ? 'bg-white dark:bg-zinc-700 text-zinc-900 dark:text-slate-100 shadow-xs' : 'text-zinc-500'
                  }`}
                >
                  <Plus className="w-3 h-3" /> Ingest Doc
                </button>
              </div>

              <button
                onClick={() => setKnowledgeBaseOpen(false)}
                className="p-1 rounded-lg text-zinc-400 hover:text-zinc-700 dark:hover:text-slate-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Modal Body */}
          <div className="p-6 max-h-[420px] overflow-y-auto">
            {activeTab === 'docs' ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs font-mono text-zinc-500 pb-2 border-b border-zinc-200 dark:border-zinc-800">
                  <span>Available Enterprise Documents ({documents.length})</span>
                  <span className="text-emerald-500 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> Vector Engine Online
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-3.5 rounded-xl bg-zinc-50 dark:bg-[#11151F] border border-zinc-200/80 dark:border-zinc-800/80 space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                          {doc.category}
                        </span>
                        <span className="font-mono text-[10px] text-zinc-400">
                          {doc.chunk_count} Chunks
                        </span>
                      </div>

                      <h4 className="font-bold text-zinc-900 dark:text-slate-100 truncate">
                        {doc.title}
                      </h4>

                      <p className="text-[11px] text-zinc-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                        {doc.content_snippet}
                      </p>

                      <div className="pt-2 border-t border-zinc-200 dark:border-zinc-800 flex items-center justify-between text-[10px] font-mono text-zinc-400">
                        <span>Updated: {doc.updated_at}</span>
                        <span className="text-indigo-500 font-semibold">Vectorized</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* Ingest Form */
              <form onSubmit={handleUploadDoc} className="space-y-4 text-xs font-sans">
                {successMessage && (
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center gap-2 font-mono">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{successMessage}</span>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-3">
                  <div className="col-span-2 space-y-1">
                    <label className="font-mono font-semibold text-zinc-700 dark:text-slate-300">
                      Document Title / Name (.md)
                    </label>
                    <input
                      type="text"
                      required
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      placeholder="e.g. OAuth 2.0 PKCE Setup Guide.md"
                      className="w-full px-3 py-2 rounded-xl bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-xs focus:outline-none focus:ring-1 focus:ring-purple-500"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-mono font-semibold text-zinc-700 dark:text-slate-300">
                      Category
                    </label>
                    <select
                      value={newCategory}
                      onChange={(e: any) => setNewCategory(e.target.value)}
                      className="w-full px-3 py-2 rounded-xl bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-xs focus:outline-none focus:ring-1 focus:ring-purple-500 font-mono"
                    >
                      <option value="API">API</option>
                      <option value="Policy">Policy</option>
                      <option value="Billing">Billing</option>
                      <option value="Security">Security</option>
                      <option value="Integration">Integration</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-mono font-semibold text-zinc-700 dark:text-slate-300">
                    Raw Document Text Content
                  </label>
                  <textarea
                    rows={6}
                    required
                    value={newContent}
                    onChange={(e) => setNewContent(e.target.value)}
                    placeholder="Paste Markdown or text content to split into vector embeddings..."
                    className="w-full p-3 rounded-xl bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-xs focus:outline-none focus:ring-1 focus:ring-purple-500 font-mono leading-relaxed resize-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-md transition-all disabled:opacity-50"
                >
                  <Upload className="w-4 h-4" />
                  <span>{isSubmitting ? 'Generating Vectors & Indexing...' : 'Index Document into ChromaDB Vector Store'}</span>
                </button>
              </form>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-3 bg-zinc-50 dark:bg-[#131722] border-t border-zinc-200/80 dark:border-zinc-800/80 flex items-center justify-between text-[11px] font-mono text-zinc-500">
            <span>Model: sentence-transformers/all-MiniLM-L6-v2</span>
            <span>Cosine Distance Matrix</span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
