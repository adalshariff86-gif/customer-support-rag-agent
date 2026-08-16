import React, { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { motion } from 'motion/react';
import {
  User,
  Cpu,
  Copy,
  Check,
  RotateCcw,
  BookOpen,
  Zap,
  Terminal,
  ExternalLink,
  Code2
} from 'lucide-react';
import { ChatMessage, SourceCitation } from '../../types';
import { useStore } from '../../store/useStore';

interface Props {
  message: ChatMessage;
}

// Helper component for Code Block with Copy feature
const FormattedContent: React.FC<{ content: string; isUser: boolean }> = ({ content, isUser }) => {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const parts = useMemo(() => {
    if (isUser) return [];

    const codeBlockRegex = /```([a-zA-Z0-9_]*)\n([\s\S]*?)```/g;
    const result = [];
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(content)) !== null) {
      if (match.index > lastIndex) {
        result.push({ type: 'text', text: content.slice(lastIndex, match.index) });
      }
      result.push({
        type: 'code',
        language: match[1] || 'bash',
        code: match[2].trim(),
      });
      lastIndex = codeBlockRegex.lastIndex;
    }

    if (lastIndex < content.length) {
      result.push({ type: 'text', text: content.slice(lastIndex) });
    }

    return result;
  }, [content, isUser]);

  if (isUser) {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }

  const handleCopyCode = (code: string, idx: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="space-y-3 font-sans leading-relaxed">
      {parts.map((part, idx) => {
        if (part.type === 'text') {
          return (
            <div key={idx} className="text-xs sm:text-sm">
              <ReactMarkdown
                components={{
                  p: ({ node, ...props }) => <p className="mb-2 last:mb-0 leading-relaxed inline-block" {...props} />,
                  ul: ({ node, ...props }) => <ul className="list-disc ml-5 mb-2 space-y-1" {...props} />,
                  ol: ({ node, ...props }) => <ol className="list-decimal ml-5 mb-2 space-y-1" {...props} />,
                  li: ({ node, ...props }) => <li className="pl-1" {...props} />,
                  strong: ({ node, ...props }) => <strong className="font-bold" {...props} />,
                  code: ({ node, inline, className, children, ...props }: any) =>
                    inline ? <code className="bg-zinc-200 dark:bg-zinc-700 px-1 py-0.5 rounded text-[11px]" {...props}>{children}</code> : <code {...props}>{children}</code>
                }}
              >
                {part.text}
              </ReactMarkdown>
            </div>
          );
        }

        if (part.type === 'code') {
          return (
            <div
              key={idx}
              className="my-3 rounded-xl bg-zinc-950 border border-zinc-800 text-slate-100 font-mono text-xs overflow-hidden shadow-md"
            >
              {/* Header bar */}
              <div className="px-3.5 py-2 bg-zinc-900/90 border-b border-zinc-800 flex items-center justify-between text-[11px] text-zinc-400">
                <span className="flex items-center gap-1.5 uppercase font-semibold text-indigo-400">
                  <Code2 className="w-3.5 h-3.5" />
                  {part.language}
                </span>
                <button
                  onClick={() => handleCopyCode(part.code, idx)}
                  className="flex items-center gap-1 px-2 py-0.5 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 transition-colors"
                >
                  {copiedIndex === idx ? (
                    <Check className="w-3 h-3 text-emerald-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                  <span>{copiedIndex === idx ? 'Copied' : 'Copy Code'}</span>
                </button>
              </div>

              {/* Code content */}
              <pre className="p-4 overflow-x-auto text-[11px] leading-normal text-emerald-300 selection:bg-indigo-500 selection:text-white">
                <code>{part.code}</code>
              </pre>
            </div>
          );
        }

        return null;
      })}
    </div>
  );
};

export const ChatMessageItem: React.FC<Props> = ({ message }) => {
  const { developerMode, setSelectedSource, sendMessage } = useStore();
  const [copied, setCopied] = useState(false);

  const isUser = message.role === 'user';

  const handleCopyText = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRetry = () => {
    if (message.content) {
      sendMessage(message.content);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`flex items-start gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {/* Avatar for Assistant */}
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#5B5CEB] to-[#3B82F6] dark:from-[#7C6CFF] dark:to-[#60A5FA] flex items-center justify-center text-white text-xs font-bold shrink-0 mt-1 shadow-sm">
          <Cpu className="w-4 h-4" />
        </div>
      )}

      <div className={`space-y-2 max-w-[92%] sm:max-w-[82%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Message Bubble Container */}
        <div
          className={`p-4 rounded-2xl text-xs sm:text-sm leading-relaxed font-sans shadow-sm ${isUser
              ? 'bg-indigo-600 text-white rounded-tr-sm'
              : 'bg-zinc-100/90 dark:bg-[#11151F] text-zinc-800 dark:text-slate-200 border border-zinc-200/80 dark:border-zinc-800/80 rounded-tl-sm'
            }`}
        >
          {/* Main Content with Code formatting */}
          <FormattedContent content={message.content} isUser={isUser} />

          {/* Sources Citation Bar (for Assistant) */}
          {!isUser && message.sources && message.sources.length > 0 && (
            <div className="pt-3 mt-3 border-t border-zinc-200/80 dark:border-zinc-800/80">
              <button
                onClick={() => setSelectedSource(message.sources![0])}
                className="flex items-center gap-2 px-3 py-2 rounded-xl bg-zinc-50/80 dark:bg-zinc-900/40 border border-zinc-200 dark:border-zinc-800/60 hover:bg-zinc-100 dark:hover:bg-zinc-800/60 hover:border-indigo-300 dark:hover:border-indigo-700 transition-all font-sans group w-full text-left"
              >
                <BookOpen className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
                <span className="text-xs font-semibold text-zinc-700 dark:text-slate-300">
                  View {message.sources.length} Source{message.sources.length > 1 ? 's' : ''}
                </span>
              </button>
            </div>
          )}
        </div>

        {/* Message Footer Actions & Developer Metrics */}
        <div className={`flex items-center gap-3 text-[10px] font-mono text-zinc-400 dark:text-slate-500 px-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span>{message.timestamp}</span>

          {!isUser && (
            <>
              {/* Copy Action */}
              <button
                onClick={handleCopyText}
                className="hover:text-zinc-700 dark:hover:text-slate-300 flex items-center gap-1 transition-colors"
                title="Copy Response"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>

              {/* Retry Action */}
              <button
                onClick={handleRetry}
                className="hover:text-zinc-700 dark:hover:text-slate-300 flex items-center gap-1 transition-colors"
                title="Retry Query"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Retry</span>
              </button>
            </>
          )}

          {/* Developer Metrics Pill */}
          {!isUser && developerMode && message.metrics && (
            <span className="flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
              <Zap className="w-3 h-3 text{message.metrics.total_latency_ms}ms -amber-500" />

            </span>
          )}
        </div>

      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-zinc-800 dark:bg-zinc-700 flex items-center justify-center text-white text-xs font-bold shrink-0 mt-1">
          <User className="w-4 h-4" />
        </div>
      )}
    </motion.div>
  );
};
