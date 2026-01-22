'use client';

import { useState, useEffect } from 'react';
import {
  listDocuments,
  listIndexedDocuments,
  indexDocument,
  deleteIndexedDocument,
  DocumentInfo,
  IndexedDocumentInfo,
} from '@/lib/api';

export default function DocumentsPage() {
  const [uploadedDocs, setUploadedDocs] = useState<DocumentInfo[]>([]);
  const [indexedDocs, setIndexedDocs] = useState<IndexedDocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [indexing, setIndexing] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      setLoading(true);
      setError(null);
      const [uploaded, indexed] = await Promise.all([
        listDocuments(),
        listIndexedDocuments(),
      ]);
      setUploadedDocs(uploaded);
      setIndexedDocs(indexed);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  }

  async function handleIndex(filename: string) {
    setIndexing(filename);
    setError(null);

    try {
      await indexDocument(filename);
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to index document');
    } finally {
      setIndexing(null);
    }
  }

  async function handleDelete(source: string) {
    if (!confirm(`Are you sure you want to delete all indexed chunks for "${source}"?`)) {
      return;
    }

    setDeleting(source);
    setError(null);

    try {
      await deleteIndexedDocument(source);
      await loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete document');
    } finally {
      setDeleting(null);
    }
  }

  function formatFileSize(bytes?: number): string {
    if (!bytes) return 'Unknown';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }

  function formatDate(dateString?: string): string {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  }

  function isIndexed(filename: string): boolean {
    return indexedDocs.some((doc) => doc.source === filename);
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-white">
        <p className="text-gray-500">Loading documents...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-black">
          Documents
        </h1>
        <button
          onClick={loadDocuments}
          className="px-4 py-2 bg-gray-200 text-black rounded-lg hover:bg-gray-300"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Uploaded Documents */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-300">
          <h2 className="text-xl font-semibold mb-4 text-black">
            Uploaded Documents
          </h2>
          {uploadedDocs.length === 0 ? (
            <p className="text-gray-500">
              No documents uploaded yet.
            </p>
          ) : (
            <div className="space-y-3">
              {uploadedDocs.map((doc) => (
                <div
                  key={doc.key}
                  className="p-3 border border-gray-300 rounded-lg"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="font-medium text-black">
                        {doc.original_filename || doc.key}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Size: {formatFileSize(doc.size)}
                      </p>
                      <p className="text-xs text-gray-500">
                        Modified: {formatDate(doc.last_modified)}
                      </p>
                      {isIndexed(doc.original_filename || doc.key) && (
                        <span className="inline-block mt-2 px-2 py-1 text-xs bg-gray-100 text-black border border-black rounded">
                          Indexed
                        </span>
                      )}
                    </div>
                    {!isIndexed(doc.original_filename || doc.key) && (
                      <button
                        onClick={() => handleIndex(doc.original_filename || doc.key)}
                        disabled={indexing === doc.key}
                        className="ml-2 px-3 py-1 text-sm bg-black text-white rounded hover:bg-gray-800 disabled:opacity-50"
                      >
                        {indexing === doc.key ? 'Indexing...' : 'Index'}
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Indexed Documents */}
        <div className="bg-white rounded-lg shadow p-6 border border-gray-300">
          <h2 className="text-xl font-semibold mb-4 text-black">
            Indexed Documents
          </h2>
          {indexedDocs.length === 0 ? (
            <p className="text-gray-500">
              No documents indexed yet. Index documents to enable Q&A.
            </p>
          ) : (
            <div className="space-y-3">
              {indexedDocs.map((doc) => (
                <div
                  key={doc.source}
                  className="p-3 border border-gray-300 rounded-lg"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="font-medium text-black">
                        {doc.source}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {doc.chunks_count} chunks
                      </p>
                      {doc.last_indexed_at && (
                        <p className="text-xs text-gray-500">
                          Indexed: {formatDate(doc.last_indexed_at)}
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => handleDelete(doc.source)}
                      disabled={deleting === doc.source}
                      className="ml-2 px-3 py-1 text-sm bg-black text-white rounded hover:bg-gray-800 disabled:opacity-50"
                    >
                      {deleting === doc.source ? 'Deleting...' : 'Delete'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

