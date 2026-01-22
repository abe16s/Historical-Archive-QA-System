// API client for backend communication

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types matching backend schemas
export interface DocumentInfo {
  key: string;
  size?: number;
  last_modified?: string;
  original_filename?: string;
  signed_url?: string;
}

export interface IndexedDocumentInfo {
  source: string;
  chunks_count: number;
  last_indexed_at?: string;
}

export interface DocumentUploadResponse {
  message: string;
  filename?: string;
  chunks_count?: number;
  file_path?: string;
}

export interface DocumentIndexResponse {
  message: string;
  filename?: string;
  chunks_count: number;
  file_path: string;
}

export interface IndexedDocumentDeleteResponse {
  source: string;
  deleted_chunks: number;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface SourceInfo {
  source: string;
  page: number | null;
  display_text: string;
  url: string;
}

export interface ChatResponse {
  response: string;
  sources: SourceInfo[];
  conversation_id: string;
  timestamp?: string;
}

export interface CitationAccuracy {
  total_citations: number;
  valid_citations: number;
  citation_accuracy: number;
  missing_sources: string[];
  invalid_citations: string[];
}

export interface ContextRelevance {
  average_similarity: number;
  min_similarity: number;
  max_similarity: number;
  relevant_chunks: number;
  total_chunks: number;
}

export interface AnswerFaithfulness {
  faithfulness_score: number;
  supported_claims: number;
  total_claims: number;
  unsupported_claims: string[];
}

export interface EvaluationMetrics {
  citation_accuracy: CitationAccuracy;
  context_relevance: ContextRelevance;
  answer_faithfulness: AnswerFaithfulness;
  overall_score: number;
  evaluation_timestamp: string;
}

export interface EvaluationRequest {
  query: string;
  answer: string;
  context_chunks: Array<Record<string, any>>;
  sources: string[];
}

export interface EvaluationResponse {
  query: string;
  answer: string;
  metrics: EvaluationMetrics;
  recommendations: string[];
}

// API functions
export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(error.detail || 'Failed to upload document');
  }

  return response.json();
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const response = await fetch(`${API_BASE_URL}/documents/list`);

  if (!response.ok) {
    throw new Error('Failed to list documents');
  }

  return response.json();
}

export async function indexDocument(filename: string): Promise<DocumentIndexResponse> {
  const response = await fetch(`${API_BASE_URL}/documents/index`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ filename }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Indexing failed' }));
    throw new Error(error.detail || 'Failed to index document');
  }

  return response.json();
}

export async function listIndexedDocuments(): Promise<IndexedDocumentInfo[]> {
  const response = await fetch(`${API_BASE_URL}/documents/indexed`);

  if (!response.ok) {
    throw new Error('Failed to list indexed documents');
  }

  return response.json();
}

export async function deleteIndexedDocument(source: string): Promise<IndexedDocumentDeleteResponse> {
  const encodedSource = encodeURIComponent(source);
  const response = await fetch(`${API_BASE_URL}/documents/indexed/${encodedSource}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Deletion failed' }));
    throw new Error(error.detail || 'Failed to delete indexed document');
  }

  return response.json();
}

export interface QuotaError {
  error: string;
  message: string;
  retry_after?: number;
  quota_limit?: number;
}

export async function sendChatMessage(
  message: string,
  conversationId?: string
): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Chat request failed' }));
    
    // Handle quota errors specially (FastAPI returns error details in 'detail' field)
    if (response.status === 429) {
      const error = errorData.detail || errorData;
      if (typeof error === 'object' && error.error === 'quota_exceeded') {
        const quotaError: QuotaError = error;
        throw new QuotaExceededError(
          quotaError.message || 'API quota exceeded',
          quotaError.retry_after,
          quotaError.quota_limit
        );
      }
    }
    
    // Handle other errors
    const errorMessage = typeof errorData.detail === 'string' 
      ? errorData.detail 
      : (errorData.detail?.message || errorData.message || 'Failed to send chat message');
    throw new Error(errorMessage);
  }

  return response.json();
}

export class QuotaExceededError extends Error {
  retryAfter?: number;
  quotaLimit?: number;

  constructor(message: string, retryAfter?: number, quotaLimit?: number) {
    super(message);
    this.name = 'QuotaExceededError';
    this.retryAfter = retryAfter;
    this.quotaLimit = quotaLimit;
  }
}

export async function evaluateResponse(
  request: EvaluationRequest
): Promise<EvaluationResponse> {
  const response = await fetch(`${API_BASE_URL}/evaluation/evaluate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Evaluation failed' }));
    throw new Error(error.detail || 'Failed to evaluate response');
  }

  return response.json();
}

export async function evaluateChatResponse(
  query: string
): Promise<EvaluationResponse> {
  const response = await fetch(`${API_BASE_URL}/evaluation/evaluate-chat?query=${encodeURIComponent(query)}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Evaluation failed' }));
    throw new Error(error.detail || 'Failed to evaluate chat response');
  }

  return response.json();
}
