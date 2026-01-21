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

export interface ChatResponse {
  response: string;
  sources: string[];
  conversation_id: string;
  timestamp?: string;
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
    const error = await response.json().catch(() => ({ detail: 'Chat request failed' }));
    throw new Error(error.detail || 'Failed to send chat message');
  }

  return response.json();
}

