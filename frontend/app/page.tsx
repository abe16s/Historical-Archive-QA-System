'use client';

import ChatInterface from '@/components/ChatInterface';
import DocumentSelector from '@/components/DocumentSelector';

export default function Home() {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-hidden">
          <ChatInterface />
        </div>
      </div>
      <div className="w-80 border-l border-gray-200 dark:border-gray-800 p-4 overflow-y-auto">
        <DocumentSelector />
      </div>
    </div>
  );
}
