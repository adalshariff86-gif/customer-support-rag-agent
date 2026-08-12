import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
} from 'axios';

import {
  SourceCitation,
  DevMetrics,
} from '../types';

// ============================================================
// ENVIRONMENT
// ============================================================

const BASE_URL = '';

const API_KEY =
  import.meta.env.VITE_FASTAPI_API_KEY || '';

// ============================================================
// TYPES
// ============================================================

export interface ChatResponsePayload {
  session_id: string;
  answer: string;
  sources: SourceCitation[];
  model: string;
  latency_ms: number;
  timestamp: string;
}

export interface NewChatResponse {
  session_id: string;
  created: boolean;
}

export interface DocumentsStatusResponse {
  collection_name: string;
  collection_exists: boolean;
  document_count: number;
}

export interface IngestionResponse {
  documents_loaded: number;
  chunks_created: number;
  vectors_stored: number;
  collection_name: string;
  elapsed_ms: number;
  already_indexed: boolean;
  message: string;
}

export interface ChatHealthResponse {
  status: string;
  service: string;
  timestamp: string;
  version: string;
}

// ============================================================
// AXIOS CLIENT
// ============================================================

export const apiClient: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,

  headers: {
    'Content-Type': 'application/json',
    'X-Client-Platform': 'ResolveHQ-Web-React',
    'X-API-Key': API_KEY,
  },
});

// ============================================================
// REQUEST INTERCEPTOR
// ============================================================

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Always attach API key to protected backend requests.
    if (API_KEY) {
      config.headers.set('X-API-Key', API_KEY);
    }

    config.headers.set(
      'X-Client-Platform',
      'ResolveHQ-Web-React'
    );

    return config;
  },

  (error) => {
    return Promise.reject(error);
  }
);

// ============================================================
// RESPONSE INTERCEPTOR
// ============================================================

apiClient.interceptors.response.use(
  (response) => {
    return response;
  },

  async (error: AxiosError) => {
    const config = error.config as
      | (InternalAxiosRequestConfig & {
        _retry?: boolean;
      })
      | undefined;

    // Retry exactly once for:
    // - timeout
    // - 5xx backend errors
    const shouldRetry =
      config &&
      !config._retry &&
      (
        error.code === 'ECONNABORTED' ||
        error.code === 'ETIMEDOUT' ||
        Boolean(
          error.response &&
          error.response.status >= 500
        )
      );

    if (shouldRetry && config) {
      config._retry = true;

      try {
        return await apiClient(config);
      } catch (retryError) {
        return Promise.reject(retryError);
      }
    }

    return Promise.reject(error);
  }
);

// ============================================================
// API SERVICE
// ============================================================

export const apiService = {

  // ----------------------------------------------------------
  // POST /chat
  // ----------------------------------------------------------

  postChat: async (
    message: string,
    session_id?: string,
  ): Promise<ChatResponsePayload> => {

    const payload: any = { message };
    if (session_id) {
      payload.session_id = session_id;
    }

    const response =
      await apiClient.post<ChatResponsePayload>(
        '/chat',
        payload
      );

    return response.data;
  },

  // ----------------------------------------------------------
  // POST /chat/new
  // ----------------------------------------------------------

  postNewChat: async (): Promise<NewChatResponse> => {

    const response =
      await apiClient.post<NewChatResponse>(
        '/chat/new'
      );

    return response.data;
  },

  // ----------------------------------------------------------
  // GET /chat/health
  // ----------------------------------------------------------

  getHealth: async (): Promise<ChatHealthResponse> => {

    const response =
      await apiClient.get<ChatHealthResponse>(
        '/chat/health'
      );

    return response.data;
  },

  // ----------------------------------------------------------
  // GET /documents/status
  // ----------------------------------------------------------

  getDocumentsStatus:
    async (): Promise<DocumentsStatusResponse> => {

      const response =
        await apiClient.get<DocumentsStatusResponse>(
          '/documents/status'
        );

      return response.data;
    },

  // ----------------------------------------------------------
  // POST /documents/ingest
  // ----------------------------------------------------------

  ingestDocuments:
    async (
      force = false
    ): Promise<IngestionResponse> => {

      const response =
        await apiClient.post<IngestionResponse>(
          '/documents/ingest',
          null,
          {
            params: {
              force,
            },
          }
        );

      return response.data;
    },
};

// ============================================================
// EXPORT
// ============================================================

export default apiService;
