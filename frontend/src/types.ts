export type Role = 'user' | 'assistant' | 'system';

export interface SourceCitation {
  id: string;
  content: string;
  score: number; // e.g. 0.9412
  metadata: {
    source?: string;
    section?: string;
    page?: number;
    updated_at?: string;
    category?: string;
    source_url?: string;
    [key: string]: any;
  };
}

export interface DevMetrics {
  embedding_time_ms: number;
  retrieval_time_ms: number;
  llm_time_ms: number;
  total_latency_ms: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  provider: string;
  model: string;
  top_k: number;
  temperature: number;
  chunks_retrieved: number;
  similarity_scores: number[];
  memory_turns_count: number;
  system_prompt_used?: string;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  role: Role;
  content: string;
  timestamp: string;
  sources?: SourceCitation[];
  metrics?: DevMetrics;
  isStreaming?: boolean;
  error?: boolean;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'offline';
  version: string;
  tests_passing: number;
  chromadb_connected: boolean;
  fastapi_connected: boolean;
  gemini_api_connected: boolean;
  indexed_documents_count: number;
  total_chunks: number;
  embedding_model: string;
  uptime_seconds: number;
}

export interface SupportDocument {
  id: string;
  title: string;
  category: 'API' | 'Policy' | 'Billing' | 'Security' | 'Integration';
  chunk_count: number;
  updated_at: string;
  size_kb: number;
  content_snippet: string;
  raw_text?: string;
}

export interface AppSettings {
  temperature: number;
  top_k: number;
  developer_mode: boolean;
  theme: 'light' | 'dark' | 'system';
  sound_enabled: boolean;
  fastapi_url: string;
  auto_scroll: boolean;
}

export interface ConversationSession {
  id: string;
  title: string;
  created_at: string;
  last_message_at: string;
  message_count: number;
  preview_text: string;
}
