'use client';

import { IndexedDocumentInfo } from '@/lib/api';
import { useState, useEffect } from 'react';

export default function DocumentSelector() {
  const [indexedDocs, setIndexedDocs] = useState<IndexedDocumentInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadIndexedDocuments();
  }, []);

  async function loadIndexedDocuments() {
    try {
      setLoading(true);
      const { listIndexedDocuments } = await import('@/lib/api');
      const data = await listIndexedDocuments();
      setIndexedDocs(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-gray-500">Loading documents...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-red-500">{error}</p>
        <button
          onClick={loadIndexedDocuments}
          className="mt-2 text-sm text-black hover:text-gray-700 font-semibold"
        >
          Retry
        </button>
      </div>
    );
  }

  if (indexedDocs.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <p className="text-gray-500">
          No indexed documents. Upload and index documents first.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-black">
          Indexed Documents
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          {indexedDocs.length} document{indexedDocs.length !== 1 ? 's' : ''} available
        </p>
      </div>
      <div className="space-y-2">
        {indexedDocs.map((doc) => (
          <div
            key={doc.source}
            className="p-3 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
          >
            <p className="text-sm font-medium text-black break-words">
              {doc.source}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {doc.chunks_count} chunk{doc.chunks_count !== 1 ? 's' : ''}
            </p>
            {doc.last_indexed_at && (
              <p className="text-xs text-gray-400 mt-1">
                Indexed: {new Date(doc.last_indexed_at).toLocaleDateString()}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

