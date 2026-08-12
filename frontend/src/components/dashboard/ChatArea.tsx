import React, {
  useState,
  useRef,
  useEffect,
} from 'react';

import { motion } from 'motion/react';

import {
  Send,
  Bot,
  Cpu,
  CornerDownLeft,
} from 'lucide-react';

import { useStore } from '../../store/useStore';
import { ChatMessageItem } from './ChatMessageItem';

export const ChatArea: React.FC = () => {
  const {
    messages,
    activeConversationId,
    isLoading,
    sendMessage,
    settings,
  } = useStore();

  const [inputText, setInputText] = useState('');

  const messagesEndRef =
    useRef<HTMLDivElement | null>(null);

  // ============================================================
  // ACTIVE MESSAGES
  // ============================================================

  const activeMessages = messages.filter(
    (message) =>
      message.conversation_id === activeConversationId
  );

  // ============================================================
  // SUGGESTED PROMPTS
  // ============================================================

  const suggestedPrompts = [
    'What is the refund policy?',
    'How long does shipping take?',
    'What is the return policy?',
    'What is the warranty policy?',
  ];

  // ============================================================
  // SCROLL
  // ============================================================

  const scrollToBottom = () => {
    if (!settings.auto_scroll) return;

    requestAnimationFrame(() => {
      messagesEndRef.current?.scrollIntoView({
        behavior: 'smooth',
      });
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // ============================================================
  // SEND MESSAGE
  // ============================================================

  const handleSubmit = async (
    event: React.FormEvent
  ) => {
    event.preventDefault();

    const text = inputText.trim();

    if (!text || isLoading) {
      return;
    }

    setInputText('');

    try {
      await sendMessage(text);
    } catch (error) {
      console.error(
        'Chat submission failed:',
        error
      );
    }
  };

  // ============================================================
  // KEYBOARD
  // ============================================================

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLTextAreaElement>
  ) => {
    if (
      event.key === 'Enter' &&
      !event.shiftKey
    ) {
      event.preventDefault();

      void handleSubmit(
        event as unknown as React.FormEvent
      );
    }
  };

  // ============================================================
  // SUGGESTED PROMPT
  // ============================================================

  const handleSuggestedPrompt = (
    prompt: string
  ) => {
    if (isLoading) return;

    void sendMessage(prompt);
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="flex flex-col h-full min-h-0">

      {/* ======================================================
          MESSAGES
      ======================================================= */}

      <div className="flex-1 min-h-0 overflow-y-auto px-4 sm:px-8 py-6 space-y-4">

        {/* EMPTY STATE */}

        {activeMessages.length === 0 && !isLoading && (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto space-y-6">

            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-[#5B5CEB] to-[#3B82F6] flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
              <Cpu className="w-6 h-6" />
            </div>

            <div className="space-y-2">

              <h3 className="text-xl font-bold text-zinc-900 dark:text-slate-100">
                Ask ResolveHQ AI
              </h3>

              <p className="text-xs sm:text-sm text-zinc-500 dark:text-slate-400">
                Every Customer Question. Resolved with
                Context. Grounded in your ChromaDB vector
                store.
              </p>

            </div>

            <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">

              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  disabled={isLoading}
                  onClick={() =>
                    handleSuggestedPrompt(prompt)
                  }
                  className="p-3 rounded-xl bg-zinc-50 dark:bg-[#11151F] border border-zinc-200/80 dark:border-zinc-800/80 hover:border-indigo-500/80 dark:hover:border-indigo-500/80 text-xs text-left text-zinc-700 dark:text-slate-300 transition-all shadow-2xs font-sans disabled:opacity-50"
                >
                  {prompt}
                </button>
              ))}

            </div>

          </div>
        )}

        {/* CHAT HISTORY */}

        {activeMessages.map((message) => (
          <ChatMessageItem
            key={message.id}
            message={message}
          />
        ))}

        {/* TYPING INDICATOR */}

        {isLoading && (
          <motion.div
            initial={{
              opacity: 0,
              y: 10,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            className="flex items-center gap-3 my-4"
          >

            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#5B5CEB] to-[#3B82F6] flex items-center justify-center text-white text-xs font-bold shrink-0">
              <Bot className="w-4 h-4" />
            </div>

            <div className="px-4 py-3 rounded-2xl bg-zinc-100 dark:bg-[#11151F] border border-zinc-200 dark:border-zinc-800 text-xs text-zinc-600 dark:text-slate-300 flex items-center gap-3 font-mono">
              <span className="animate-pulse">
                Embedding & Querying ChromaDB Vector Index...
              </span>
            </div>

          </motion.div>
        )}

        {/* SCROLL ANCHOR */}

        <div ref={messagesEndRef} />

      </div>

      {/* ======================================================
          INPUT
      ======================================================= */}

      <div className="shrink-0 p-4 bg-white/90 dark:bg-[#0A0C10]/90 border-t border-zinc-200/80 dark:border-zinc-800/80 backdrop-blur-md">

        <div className="max-w-3xl mx-auto">

          <form
            onSubmit={handleSubmit}
            className="relative"
          >

            <textarea
              rows={2}
              value={inputText}
              onChange={(event) =>
                setInputText(event.target.value)
              }
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              placeholder="Ask a customer support query..."
              className="w-full pl-4 pr-12 py-3 rounded-2xl bg-zinc-50 dark:bg-[#11151F] border border-zinc-200/80 dark:border-zinc-800/80 text-xs sm:text-sm text-zinc-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-none font-sans disabled:opacity-60"
            />

            <button
              type="submit"
              disabled={
                isLoading ||
                !inputText.trim()
              }
              className="absolute right-3 bottom-3 p-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white transition-all disabled:opacity-40 shadow-md shadow-indigo-500/20"
              title="Send Query (Enter)"
            >
              <Send className="w-4 h-4" />
            </button>

          </form>

          {/* INFO BAR */}

          <div className="flex items-center justify-between text-[10px] font-mono text-zinc-400 dark:text-slate-500 px-2 pt-2">

            <span className="flex items-center gap-1">
              <CornerDownLeft className="w-3 h-3" />
              Press Enter to send, Shift+Enter for newline
            </span>

            <span>
              Temp: {settings.temperature} | Top-K:{' '}
              {settings.top_k}
            </span>

          </div>

        </div>

      </div>

    </div>
  );
};
