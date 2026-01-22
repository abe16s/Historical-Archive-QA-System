'use client';

import { useState } from 'react';
import { evaluateResponse, evaluateChatResponse, EvaluationResponse } from '@/lib/api';

export default function EvaluationPage() {
  const [mode, setMode] = useState<'manual' | 'chat'>('manual');
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [contextChunks, setContextChunks] = useState('');
  const [sources, setSources] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<EvaluationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleEvaluate() {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      if (mode === 'chat') {
        if (!query.trim()) {
          throw new Error('Query is required');
        }
        const response = await evaluateChatResponse(query);
        setResult(response);
      } else {
        if (!query.trim() || !answer.trim()) {
          throw new Error('Query and answer are required');
        }
        
        let parsedContextChunks: Array<Record<string, any>> = [];
        if (contextChunks.trim()) {
          try {
            parsedContextChunks = JSON.parse(contextChunks);
          } catch {
            throw new Error('Context chunks must be valid JSON');
          }
        }

        const parsedSources = sources
          .split(',')
          .map(s => s.trim())
          .filter(s => s.length > 0);

        const response = await evaluateResponse({
          query: query.trim(),
          answer: answer.trim(),
          context_chunks: parsedContextChunks,
          sources: parsedSources,
        });
        setResult(response);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Evaluation failed');
    } finally {
      setLoading(false);
    }
  }

  function formatScore(score: number): string {
    return (score * 100).toFixed(1) + '%';
  }

  function getScoreColor(score: number): string {
    if (score >= 0.8) return 'text-green-600 dark:text-green-400';
    if (score >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  }

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          RAG Evaluation
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Evaluate RAG responses for factual grounding, citation accuracy, and context relevance
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Evaluation Mode
          </label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="manual"
                checked={mode === 'manual'}
                onChange={(e) => setMode(e.target.value as 'manual' | 'chat')}
                className="mr-2"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Manual Evaluation</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="chat"
                checked={mode === 'chat'}
                onChange={(e) => setMode(e.target.value as 'manual' | 'chat')}
                className="mr-2"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">Chat Evaluation</span>
            </label>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Query *
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter the question/query"
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
              rows={3}
              disabled={loading}
            />
          </div>

          {mode === 'manual' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Answer *
                </label>
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Enter the generated answer"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  rows={5}
                  disabled={loading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Context Chunks (JSON)
                </label>
                <textarea
                  value={contextChunks}
                  onChange={(e) => setContextChunks(e.target.value)}
                  placeholder='[{"content": "...", "metadata": {...}}, ...]'
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white font-mono text-sm"
                  rows={6}
                  disabled={loading}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Optional: JSON array of context chunks used to generate the answer
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Sources (comma-separated)
                </label>
                <input
                  type="text"
                  value={sources}
                  onChange={(e) => setSources(e.target.value)}
                  placeholder="source1.pdf, source2.pdf"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  disabled={loading}
                />
              </div>
            </>
          )}

          <button
            onClick={handleEvaluate}
            disabled={loading || (mode === 'manual' && (!query.trim() || !answer.trim())) || (mode === 'chat' && !query.trim())}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Evaluating...' : 'Evaluate Response'}
          </button>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}
      </div>

      {result && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Evaluation Results
            </h2>

            <div className="mb-6">
              <div className="flex items-center justify-between p-4 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg">
                <span className="text-lg font-semibold text-gray-900 dark:text-white">
                  Overall Score
                </span>
                <span className={`text-3xl font-bold ${getScoreColor(result.metrics.overall_score)}`}>
                  {formatScore(result.metrics.overall_score)}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Citation Accuracy
                </h3>
                <p className={`text-2xl font-bold ${getScoreColor(result.metrics.citation_accuracy.citation_accuracy)}`}>
                  {formatScore(result.metrics.citation_accuracy.citation_accuracy)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {result.metrics.citation_accuracy.valid_citations} / {result.metrics.citation_accuracy.total_citations} valid
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Context Relevance
                </h3>
                <p className={`text-2xl font-bold ${getScoreColor(result.metrics.context_relevance.average_similarity)}`}>
                  {formatScore(result.metrics.context_relevance.average_similarity)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {result.metrics.context_relevance.relevant_chunks} / {result.metrics.context_relevance.total_chunks} relevant
                </p>
              </div>

              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Answer Faithfulness
                </h3>
                <p className={`text-2xl font-bold ${getScoreColor(result.metrics.answer_faithfulness.faithfulness_score)}`}>
                  {formatScore(result.metrics.answer_faithfulness.faithfulness_score)}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {result.metrics.answer_faithfulness.supported_claims} / {result.metrics.answer_faithfulness.total_claims} supported
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Citation Accuracy Details
                </h3>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Total Citations:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{result.metrics.citation_accuracy.total_citations}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Valid Citations:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{result.metrics.citation_accuracy.valid_citations}</span>
                  </div>
                  {result.metrics.citation_accuracy.missing_sources.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Missing Sources:</p>
                      <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400">
                        {result.metrics.citation_accuracy.missing_sources.map((source, i) => (
                          <li key={i}>{source}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {result.metrics.citation_accuracy.invalid_citations.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Invalid Citations:</p>
                      <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400">
                        {result.metrics.citation_accuracy.invalid_citations.map((citation, i) => (
                          <li key={i}>{citation}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Context Relevance Details
                </h3>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Average Similarity:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{formatScore(result.metrics.context_relevance.average_similarity)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Min Similarity:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{formatScore(result.metrics.context_relevance.min_similarity)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Max Similarity:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{formatScore(result.metrics.context_relevance.max_similarity)}</span>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Answer Faithfulness Details
                </h3>
                <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">Supported Claims:</span>
                    <span className="font-medium text-gray-900 dark:text-white">{result.metrics.answer_faithfulness.supported_claims} / {result.metrics.answer_faithfulness.total_claims}</span>
                  </div>
                  {result.metrics.answer_faithfulness.unsupported_claims.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Unsupported Claims:</p>
                      <ul className="list-disc list-inside text-sm text-gray-600 dark:text-gray-400">
                        {result.metrics.answer_faithfulness.unsupported_claims.map((claim, i) => (
                          <li key={i}>{claim}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>

              {result.recommendations.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    Recommendations
                  </h3>
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 dark:text-gray-300">
                      {result.recommendations.map((rec, i) => (
                        <li key={i}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Evaluated Answer
            </h3>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <p className="text-gray-900 dark:text-white whitespace-pre-wrap">{result.answer}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
