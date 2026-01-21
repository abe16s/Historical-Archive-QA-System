'use client';

import { useState } from 'react';
import ChatInterface from '@/components/ChatInterface';
import DocumentSelector from '@/components/DocumentSelector';

export default function Home() {
  const [selectedSources, setSelectedSources] = useState<string[]>([]);

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-950">
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-hidden">
          <ChatInterface selectedSources={selectedSources} />
        </div>
      </div>
      <div className="w-80 border-l border-gray-200 dark:border-gray-800 p-4 overflow-y-auto">
        <DocumentSelector
          selectedSources={selectedSources}
          onSelectionChange={setSelectedSources}
        />
      </div>
    </div>
  );
}
