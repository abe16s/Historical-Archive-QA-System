'use client';

import { useState, useRef, useEffect } from 'react';
import { sendChatMessage, ChatResponse } from '@/lib/api';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp?: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response: ChatResponse = await sendChatMessage(
        userMessage,
        conversationId
      );

      setConversationId(response.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.response,
          sources: response.sources,
          timestamp: response.timestamp,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Failed to get response'}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function clearChat() {
    setMessages([]);
    setConversationId(undefined);
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 mt-8">
            <p className="text-lg">Start a conversation</p>
            <p className="text-sm mt-2">
              Ask questions about your indexed documents
            </p>
          </div>
        ) : (
          messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-3xl rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white'
                }`}
              >
                {message.role === 'user' ? (
                  <p className="whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                        li: ({ children }) => <li className="mb-1">{children}</li>,
                        h1: ({ children }) => <h1 className="text-xl font-bold mb-2 mt-3 first:mt-0">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3 first:mt-0">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-base font-bold mb-2 mt-2 first:mt-0">{children}</h3>,
                        code: ({ children, className }) => {
                          const isInline = !className;
                          return isInline ? (
                            <code className="bg-gray-200 dark:bg-gray-700 px-1 py-0.5 rounded text-sm">{children}</code>
                          ) : (
                            <code className="block bg-gray-200 dark:bg-gray-700 p-2 rounded text-sm overflow-x-auto">{children}</code>
                          );
                        },
                        pre: ({ children }) => <pre className="mb-2">{children}</pre>,
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic my-2">
                            {children}
                          </blockquote>
                        ),
                        a: ({ children, href }) => (
                          <a href={href} className="text-blue-600 dark:text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">
                            {children}
                          </a>
                        ),
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                )}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600">
                    <p className="text-xs font-semibold mb-2 text-gray-700 dark:text-gray-300">
                      Sources ({message.sources.length}):
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {message.sources.map((source, i) => (
                        <span
                          key={i}
                          className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 border border-blue-200 dark:border-blue-800"
                        >
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-2">
              <p className="text-gray-500 dark:text-gray-400">Thinking...</p>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t border-gray-200 dark:border-gray-700 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-800 dark:text-white"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
          {messages.length > 0 && (
            <button
              type="button"
              onClick={clearChat}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600"
            >
              Clear
            </button>
          )}
        </form>
      </div>
    </div>
  );
}

