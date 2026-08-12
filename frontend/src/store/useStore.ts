import { create } from 'zustand';
import { apiService } from '../services/api';
import {
  ChatMessage,
  SourceCitation,
  HealthStatus,
  SupportDocument,
  AppSettings,
  ConversationSession,
} from '../types';

interface State {
  // Navigation & Views
  activeTab: 'landing' | 'app';
  setActiveTab: (tab: 'landing' | 'app') => void;

  // Theme
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;

  // Developer Mode & Side Panels
  developerMode: boolean;
  setDeveloperMode: (enabled: boolean) => void;
  toggleDeveloperMode: () => void;

  isSourcesPanelOpen: boolean;
  setSourcesPanelOpen: (open: boolean) => void;

  selectedSource: SourceCitation | null;
  setSelectedSource: (source: SourceCitation | null) => void;

  isDeveloperDrawerOpen: boolean;
  setDeveloperDrawerOpen: (open: boolean) => void;

  isKnowledgeBaseOpen: boolean;
  setKnowledgeBaseOpen: (open: boolean) => void;

  isSettingsOpen: boolean;
  setSettingsOpen: (open: boolean) => void;

  isSidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;

  // Settings
  settings: AppSettings;
  updateSettings: (newSettings: Partial<AppSettings>) => void;

  // Chat & Session State
  activeConversationId: string;
  conversations: ConversationSession[];
  messages: ChatMessage[];
  isLoading: boolean;

  // Health & Knowledge Base
  healthStatus: HealthStatus | null;
  documents: SupportDocument[];

  // Actions
  sendMessage: (userMessageText: string) => Promise<void>;
  createNewConversation: () => Promise<void>;
  switchConversation: (id: string) => void;
  fetchHealthStatus: () => Promise<void>;
  fetchDocuments: () => Promise<void>;
  addDocument: (
    title: string,
    content: string,
    category?: SupportDocument['category']
  ) => Promise<boolean>;
}

// ─────────────────────────────────────────────
// Theme helper
// ─────────────────────────────────────────────

export const applyThemeClass = (
  theme: 'light' | 'dark' | 'system'
) => {
  if (typeof window === 'undefined') return;

  const root = document.documentElement;

  let isDark = theme === 'dark';

  if (theme === 'system') {
    isDark = window
      .matchMedia('(prefers-color-scheme: dark)')
      .matches;
  }

  if (isDark) {
    root.classList.add('dark');
  } else {
    root.classList.remove('dark');
  }
};

// ─────────────────────────────────────────────
// Initial theme
// ─────────────────────────────────────────────

const storedTheme =
  typeof window !== 'undefined'
    ? localStorage.getItem('resolvehq_theme')
    : null;

const initialTheme: 'light' | 'dark' | 'system' =
  storedTheme === 'light' ||
    storedTheme === 'dark' ||
    storedTheme === 'system'
    ? storedTheme
    : 'dark';

applyThemeClass(initialTheme);

// ─────────────────────────────────────────────
// Zustand Store
// ─────────────────────────────────────────────

export const useStore = create<State>((set, get) => ({
  // ───────────────────────────────────────────
  // Navigation
  // ───────────────────────────────────────────

  activeTab: 'landing',

  setActiveTab: (tab) => {
    set({ activeTab: tab });
  },

  // ───────────────────────────────────────────
  // Theme
  // ───────────────────────────────────────────

  theme: initialTheme,

  setTheme: (theme) => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('resolvehq_theme', theme);
    }

    applyThemeClass(theme);

    set({ theme });
  },

  // ───────────────────────────────────────────
  // Developer Mode
  // ───────────────────────────────────────────

  developerMode: true,

  setDeveloperMode: (enabled) => {
    set({ developerMode: enabled });
  },

  toggleDeveloperMode: () => {
    set((state) => ({
      developerMode: !state.developerMode,
    }));
  },

  // ───────────────────────────────────────────
  // Sources Panel
  // ───────────────────────────────────────────

  isSourcesPanelOpen: false,

  setSourcesPanelOpen: (open) => {
    set({ isSourcesPanelOpen: open });
  },

  selectedSource: null,

  setSelectedSource: (source) => {
    if (source) {
      set({
        selectedSource: source,
        isSourcesPanelOpen: true,
      });
    } else {
      set({
        selectedSource: null,
      });
    }
  },

  // ───────────────────────────────────────────
  // Developer Drawer
  // ───────────────────────────────────────────

  isDeveloperDrawerOpen: false,

  setDeveloperDrawerOpen: (open) => {
    set({ isDeveloperDrawerOpen: open });
  },

  // ───────────────────────────────────────────
  // Knowledge Base
  // ───────────────────────────────────────────

  isKnowledgeBaseOpen: false,

  setKnowledgeBaseOpen: (open) => {
    set({ isKnowledgeBaseOpen: open });
  },

  // ───────────────────────────────────────────
  // Settings
  // ───────────────────────────────────────────

  isSettingsOpen: false,

  setSettingsOpen: (open) => {
    set({ isSettingsOpen: open });
  },

  // ───────────────────────────────────────────
  // Sidebar
  // ───────────────────────────────────────────

  isSidebarCollapsed: false,

  setSidebarCollapsed: (collapsed) => {
    set({ isSidebarCollapsed: collapsed });
  },

  toggleSidebar: () => {
    set((state) => ({
      isSidebarCollapsed: !state.isSidebarCollapsed,
    }));
  },

  // ───────────────────────────────────────────
  // App Settings
  // ───────────────────────────────────────────

  settings: {
    temperature: 0.2,
    top_k: 4,
    developer_mode: true,
    theme: initialTheme,
    sound_enabled: true,
    fastapi_url: 'http://127.0.0.1:8000',
    auto_scroll: true,
  },

  updateSettings: (newSettings) => {
    set((state) => ({
      settings: {
        ...state.settings,
        ...newSettings,
      },
    }));
  },

  // ───────────────────────────────────────────
  // Chat State
  // ───────────────────────────────────────────

  activeConversationId: '',
  conversations: [],
  messages: [],
  isLoading: false,

  // ───────────────────────────────────────────
  // Health / Documents
  // ───────────────────────────────────────────

  healthStatus: null,
  documents: [],

  // ───────────────────────────────────────────
  // Send Chat Message
  // ───────────────────────────────────────────

  sendMessage: async (userMessageText: string) => {
    const text = userMessageText.trim();

    if (!text || get().isLoading) {
      return;
    }

    // ----------------------------------------------------------
    // Make sure we have an active backend session
    // ----------------------------------------------------------

    let convId = get().activeConversationId;

    if (!convId) {
      try {
        const session = await apiService.postNewChat();

        convId = session.session_id;

        const now = new Date().toISOString();

        const newConversation: ConversationSession = {
          id: convId,
          title: 'New Conversation',
          created_at: now,
          last_message_at: now,
          message_count: 0,
          preview_text:
            'Start typing to query RAG knowledge base...',
        };

        set((state) => ({
          activeConversationId: convId,
          conversations: [
            newConversation,
            ...state.conversations,
          ],
        }));
      } catch (error) {
        console.error(
          'Failed to create chat session:',
          error
        );

        return;
      }
    }

    // ----------------------------------------------------------
    // Create message IDs
    // ----------------------------------------------------------

    const userMsgId = `msg-${Date.now()}`;
    const assistantMsgId = `msg-ast-${Date.now()}`;

    // ----------------------------------------------------------
    // Create user message
    // ----------------------------------------------------------

    const userMessage: ChatMessage = {
      id: userMsgId,
      conversation_id: convId,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };

    // ----------------------------------------------------------
    // SHOW USER MESSAGE IMMEDIATELY
    // ----------------------------------------------------------

    set((state) => ({
      messages: [
        ...state.messages,
        userMessage,
      ],
      isLoading: true,
      activeConversationId: convId,
    }));

    // ----------------------------------------------------------
    // CALL BACKEND
    // ----------------------------------------------------------

    try {
      const data = await apiService.postChat(
        text,
        convId
      );

      // --------------------------------------------------------
      // Create assistant message
      // --------------------------------------------------------

      const assistantMessage: ChatMessage = {
        id: assistantMsgId,
        conversation_id:
          data.session_id || convId,
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        sources: data.sources || [],
        metrics: {
          embedding_time_ms: 0,
          retrieval_time_ms: 0,
          llm_time_ms: data.latency_ms || 0,
          total_latency_ms: data.latency_ms || 0,
          prompt_tokens: 0,
          completion_tokens: 0,
          total_tokens: 0,
          provider: 'FastAPI',
          model: data.model || 'gemini',
          top_k: get().settings.top_k || 4,
          temperature: get().settings.temperature || 0.2,
          chunks_retrieved: (data.sources || []).length,
          similarity_scores: (data.sources || []).map(s => s.score || 0),
          memory_turns_count: 0
        },
      };

      // --------------------------------------------------------
      // UPDATE STORE
      // --------------------------------------------------------

      set((state) => {
        const updatedConversations =
          state.conversations.map(
            (conversation) => {
              if (conversation.id !== convId) {
                return conversation;
              }

              const conversationTitle =
                conversation.title ===
                  'New Conversation'
                  ? text.slice(0, 32) +
                  (text.length > 32 ? '...' : '')
                  : conversation.title;

              return {
                ...conversation,
                title: conversationTitle,
                last_message_at:
                  new Date().toISOString(),
                message_count:
                  conversation.message_count + 2,
                preview_text: text,
              };
            }
          );

        return {
          messages: [
            ...state.messages,
            assistantMessage,
          ],
          conversations:
            updatedConversations,
          isLoading: false,
          activeConversationId: convId,
        };
      });
    } catch (error) {
      // --------------------------------------------------------
      // HANDLE BACKEND ERROR
      // --------------------------------------------------------

      console.error(
        'Failed to send message:',
        error
      );

      const errorMessage: ChatMessage = {
        id: assistantMsgId,
        conversation_id: convId,
        role: 'assistant',
        content:
          'An error occurred while querying the ResolveHQ RAG engine. Please verify backend service availability and API authentication.',
        timestamp:
          new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          }),
        error: true,
      };

      set((state) => ({
        messages: [
          ...state.messages,
          errorMessage,
        ],
        isLoading: false,
        activeConversationId: convId,
      }));
    }
  },

  // ───────────────────────────────────────────
  // Create New Conversation
  // ───────────────────────────────────────────

  createNewConversation: async () => {
    try {
      const data =
        await apiService.postNewChat();

      const newId = data.session_id;

      const now = new Date().toISOString();

      const newSession: ConversationSession = {
        id: newId,
        title: 'New Conversation',
        created_at: now,
        last_message_at: now,
        message_count: 0,
        preview_text:
          'Start typing to query RAG knowledge base...',
      };

      set((state) => ({
        conversations: [
          newSession,
          ...state.conversations,
        ],
        activeConversationId: newId,
        messages: [],
      }));
    } catch (error) {
      console.error(
        'Failed to create new conversation:',
        error
      );
    }
  },

  // ───────────────────────────────────────────
  // Switch Conversation
  // ───────────────────────────────────────────

  switchConversation: (id) => {
    set({
      activeConversationId: id,
      messages: [],
    });
  },

  // ───────────────────────────────────────────
  // Health Status
  // ───────────────────────────────────────────

  fetchHealthStatus: async () => {
    try {
      const status =
        await apiService.getHealth();

      const healthStatus: HealthStatus = {
        status:
          status.status === 'healthy'
            ? 'healthy'
            : status.status === 'degraded'
              ? 'degraded'
              : 'offline',

        version: status.version,

        // These values are not returned by /chat/health.
        // They are kept as defaults because HealthStatus
        // currently expects them.
        tests_passing: 0,
        chromadb_connected: false,
        fastapi_connected: true,
        gemini_api_connected: false,
        indexed_documents_count: 0,
        total_chunks: 0,
        embedding_model: 'unknown',
        uptime_seconds: 0,
      };

      set({
        healthStatus,
      });
    } catch (err) {
      console.warn(
        'Could not fetch health status:',
        err
      );

      set({
        healthStatus: null,
      });
    }
  },

  // ───────────────────────────────────────────
  // Documents
  // ───────────────────────────────────────────

  fetchDocuments: async () => {
    try {
      const status =
        await apiService.getDocumentsStatus();

      const documents: SupportDocument[] =
        status.collection_exists
          ? [
            {
              id: status.collection_name,
              title: 'Knowledge Base',
              category: 'API',
              chunk_count:
                status.document_count,
              updated_at:
                new Date().toISOString(),
              size_kb: 0,
              content_snippet:
                `${status.document_count} indexed documents`,
            },
          ]
          : [];

      set({
        documents,
      });
    } catch (error) {
      console.warn(
        'Could not fetch document status:',
        error
      );

      set({
        documents: [],
      });
    }
  },

  // ───────────────────────────────────────────
  // Add / Ingest Document
  // ───────────────────────────────────────────

  addDocument: async (
    _title,
    _content,
    _category = 'API'
  ) => {
    try {
      // Your current backend does not expose
      // POST /documents.
      //
      // It exposes POST /documents/ingest,
      // which indexes files already placed in
      // data/documents/.

      await apiService.ingestDocuments(true);

      await get().fetchDocuments();
      await get().fetchHealthStatus();

      return true;
    } catch (error) {
      console.error(
        'Failed to ingest documents:',
        error
      );

      return false;
    }
  },
}));
