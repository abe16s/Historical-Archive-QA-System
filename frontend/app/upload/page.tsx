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
    <div className="max-w-2xl mx-auto p-6 bg-white">
      <h1 className="text-3xl font-bold mb-6 text-black">
        Upload Document
      </h1>

      <div className="bg-white rounded-lg shadow p-6 space-y-4 border border-gray-300">
        <div>
          <label className="block text-sm font-medium text-black mb-2">
            Select Document
          </label>
          <input
            type="file"
            onChange={handleFileChange}
            accept=".pdf,.txt,.md"
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-gray-100 file:text-black hover:file:bg-gray-200"
            disabled={uploading || indexing}
          />
          <p className="mt-1 text-xs text-gray-500">
            Supported formats: PDF, TXT, MD
          </p>
        </div>

        <div className="flex items-center">
          <input
            type="checkbox"
            id="autoIndex"
            checked={autoIndex}
            onChange={(e) => setAutoIndex(e.target.checked)}
            className="w-4 h-4 text-black border-gray-300 rounded focus:ring-black"
            disabled={uploading || indexing}
          />
          <label
            htmlFor="autoIndex"
            className="ml-2 text-sm text-black"
          >
            Automatically index after upload
          </label>
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading || indexing}
          className="w-full px-4 py-2 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Uploading...' : indexing ? 'Indexing...' : 'Upload'}
        </button>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {uploadResult && (
          <div className="p-4 bg-gray-50 border border-gray-300 rounded-lg">
            <p className="text-sm font-medium text-black mb-2">
              {uploadResult.message}
            </p>
            {uploadResult.filename && (
              <p className="text-xs text-gray-600">
                Filename: {uploadResult.filename}
              </p>
            )}
            {uploadResult.chunks_count !== undefined && (
              <p className="text-xs text-gray-600">
                Chunks: {uploadResult.chunks_count}
              </p>
            )}
            {uploadResult.filename && !uploadResult.chunks_count && (
              <button
                onClick={() => handleIndex(uploadResult.filename!)}
                disabled={indexing}
                className="mt-2 px-3 py-1 text-xs bg-black text-white rounded hover:bg-gray-800 disabled:opacity-50"
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

