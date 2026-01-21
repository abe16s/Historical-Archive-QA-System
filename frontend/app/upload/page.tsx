'use client';

import { useState } from 'react';
import { uploadDocument, indexDocument, DocumentUploadResponse } from '@/lib/api';

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [indexing, setIndexing] = useState(false);
  const [uploadResult, setUploadResult] = useState<DocumentUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [autoIndex, setAutoIndex] = useState(false);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadResult(null);
      setError(null);
    }
  }

  async function handleUpload() {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const result = await uploadDocument(file);
      setUploadResult(result);

      if (autoIndex && result.filename) {
        await handleIndex(result.filename);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  async function handleIndex(filename: string) {
    setIndexing(true);
    setError(null);

    try {
      const result = await indexDocument(filename);
      setUploadResult((prev) =>
        prev
          ? {
              ...prev,
              chunks_count: result.chunks_count,
              message: result.message,
            }
          : null
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Indexing failed');
    } finally {
      setIndexing(false);
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6 text-gray-900 dark:text-white">
        Upload Document
      </h1>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Select Document
          </label>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.txt,.md"
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-gray-700 dark:file:text-gray-300"
            disabled={uploading || indexing}
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            Supported formats: PDF, TXT, MD
          </p>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="autoIndex"
            checked={autoIndex}
            onChange={(e) => setAutoIndex(e.target.checked)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            disabled={uploading || indexing}
          />
          <label
            htmlFor="autoIndex"
            className="ml-2 text-sm text-gray-700 dark:text-gray-300"
          >
            Automatically index after upload
          </label>
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading || indexing}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Uploading...' : indexing ? 'Indexing...' : 'Upload'}
        </button>

        {error && (
          <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}

        {uploadResult && (
          <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <p className="text-sm font-medium text-green-800 dark:text-green-200 mb-2">
              {uploadResult.message}
            </p>
            {uploadResult.filename && (
              <p className="text-xs text-green-700 dark:text-green-300">
                Filename: {uploadResult.filename}
              </p>
            )}
            {uploadResult.chunks_count !== undefined && (
              <p className="text-xs text-green-700 dark:text-green-300">
                Chunks: {uploadResult.chunks_count}
              </p>
            )}
            {uploadResult.filename && !uploadResult.chunks_count && (
              <button
                onClick={() => handleIndex(uploadResult.filename!)}
                disabled={indexing}
                className="mt-2 px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
              >
                {indexing ? 'Indexing...' : 'Index Document'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

