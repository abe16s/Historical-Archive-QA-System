# Historical Archive QA System - Frontend

A Next.js frontend for the Historical Archive QA System, providing a user-friendly interface for document management and question-answering.

## Features

- **Document Upload**: Upload PDF, TXT, and MD files
- **Document Indexing**: Index uploaded documents for Q&A
- **Document Management**: View and manage uploaded and indexed documents
- **Document Selection**: Select/deselect specific documents for answering questions
- **Chat Interface**: Interactive Q&A with conversation history and source citations
- **RAG Evaluation**: Evaluate RAG responses for factual grounding, citation accuracy, and context relevance

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create a `.env.local` file in the `frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Adjust the URL if your backend is running on a different host/port.

### 3. Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── documents/         # Documents management page
│   ├── upload/           # Document upload page
│   ├── evaluation/       # RAG evaluation page
│   ├── layout.tsx        # Root layout with fixed navigation
│   ├── page.tsx          # Chat page (home)
│   └── globals.css       # Global styles
├── components/
│   ├── ChatInterface.tsx      # Chat UI component with fixed input
│   ├── DocumentSelector.tsx   # Document selection sidebar component
│   └── Navigation.tsx         # Fixed navigation bar
├── lib/
│   └── api.ts            # API client functions
└── package.json
```

## Usage

1. **Upload Documents**: Navigate to the Upload page and select a document to upload. Optionally enable auto-indexing.

2. **Manage Documents**: Go to the Documents page to:
   - View all uploaded documents
   - Index documents (if not auto-indexed)
   - View indexed documents with chunk counts
   - Delete indexed documents

3. **Ask Questions**: On the home page (Chat):
   - Select which indexed documents to use for answering (via sidebar)
   - Type your question and get answers with source citations
   - Conversation history is maintained automatically
   - Fixed layout: navbar at top, sidebar on right, chat input at bottom

4. **Evaluate Responses**: Navigate to the Evaluation page to:
   - Evaluate RAG responses in manual mode (provide query, answer, context, sources)
   - Evaluate responses in chat mode (automatically evaluates chat responses)
   - View detailed metrics: citation accuracy, context relevance, answer faithfulness
   - Get recommendations for improving response quality

## API Integration

The frontend communicates with the FastAPI backend through the following endpoints:

- `POST /documents/upload` - Upload a document
- `GET /documents/list` - List uploaded documents
- `POST /documents/index` - Index a document
- `GET /documents/indexed` - List indexed documents
- `DELETE /documents/indexed/{source}` - Delete indexed document
- `POST /chat/` - Send chat message and get response
- `POST /evaluation/evaluate` - Evaluate RAG response (manual mode)
- `POST /evaluation/evaluate-chat` - Evaluate chat response (chat mode)

## UI/UX Features

- **Fixed Layout**: 
  - Fixed navigation bar at the top
  - Fixed sidebar on the right for document selection
  - Fixed chat input at the bottom
  - Only chat history is scrollable
- **Color Scheme**: White background with black buttons and highlights for clean, modern appearance
- **Responsive Design**: Optimized for different screen sizes

## Technologies

- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Hooks** - State management
- **React Markdown** - Markdown rendering for chat responses
