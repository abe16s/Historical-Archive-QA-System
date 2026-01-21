'use client';

import { IndexedDocumentInfo } from '@/lib/api';
import { useState, useEffect } from 'react';

interface DocumentSelectorProps {
  selectedSources: string[];
  onSelectionChange: (sources: string[]) => void;
}

export default function DocumentSelector({
  selectedSources,
  onSelectionChange,
}: DocumentSelectorProps) {
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

  function toggleDocument(source: string) {
    if (selectedSources.includes(source)) {
      onSelectionChange(selectedSources.filter((s) => s !== source));
    } else {
      onSelectionChange([...selectedSources, source]);
    }
  }

  function selectAll() {
    onSelectionChange(indexedDocs.map((doc) => doc.source));
  }

  function deselectAll() {
    onSelectionChange([]);
  }

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <p className="text-gray-500 dark:text-gray-400">Loading documents...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <p className="text-red-500">{error}</p>
        <button
          onClick={loadIndexedDocuments}
          className="mt-2 text-sm text-blue-600 hover:text-blue-800"
        >
          Retry
        </button>
      </div>
    );
  }

  if (indexedDocs.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <p className="text-gray-500 dark:text-gray-400">
          No indexed documents. Upload and index documents first.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Select Documents for Answering
        </h3>
        <div className="flex gap-2">
          <button
            onClick={selectAll}
            className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
          >
            Select All
          </button>
          <button
            onClick={deselectAll}
            className="text-sm text-gray-600 hover:text-gray-800 dark:text-gray-400"
          >
            Deselect All
          </button>
        </div>
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {indexedDocs.map((doc) => (
          <label
            key={doc.source}
            className="flex items-center p-2 rounded hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
          >
            <input
              type="checkbox"
              checked={selectedSources.includes(doc.source)}
              onChange={() => toggleDocument(doc.source)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <div className="ml-3 flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {doc.source}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {doc.chunks_count} chunks
              </p>
            </div>
          </label>
        ))}
      </div>
      {selectedSources.length > 0 && (
        <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          {selectedSources.length} of {indexedDocs.length} documents selected
        </p>
      )}
    </div>
  );
}

