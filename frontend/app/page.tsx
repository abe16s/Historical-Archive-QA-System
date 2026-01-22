'use client';

import ChatInterface from '@/components/ChatInterface';
import DocumentSelector from '@/components/DocumentSelector';

export default function Home() {
  return (
    <div className="flex h-[calc(100vh-4rem)] bg-white">
      <div className="flex-1 flex flex-col pr-80">
        <ChatInterface />
      </div>
      <div className="fixed right-0 top-16 bottom-0 w-80 border-l border-gray-300 bg-white overflow-y-auto">
        <div className="p-4">
          <DocumentSelector />
        </div>
      </div>
    </div>
  );
}
