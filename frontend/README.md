# Historical Archive QA System - Frontend

A Next.js frontend for the Historical Archive QA System, providing a user-friendly interface for document management and question-answering.

## Features

- **Document Upload**: Upload PDF, TXT, and MD files
- **Document Indexing**: Index uploaded documents for Q&A
- **Document Management**: View and manage uploaded and indexed documents
- **Document Selection**: Select/deselect specific documents for answering questions
- **Chat Interface**: Interactive Q&A with conversation history and source citations

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
│   ├── api/              # API route handlers
│   ├── documents/         # Documents management page
│   ├── upload/           # Document upload page
│   ├── layout.tsx        # Root layout with navigation
│   ├── page.tsx          # Chat page (home)
│   └── globals.css       # Global styles
├── components/
│   ├── ChatInterface.tsx      # Chat UI component
│   ├── DocumentSelector.tsx   # Document selection component
│   └── Navigation.tsx         # Navigation bar
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
   - Select which indexed documents to use for answering
   - Type your question and get answers with source citations
   - Conversation history is maintained automatically

## API Integration

The frontend communicates with the FastAPI backend through the following endpoints:

- `POST /documents/upload` - Upload a document
- `GET /documents/list` - List uploaded documents
- `POST /documents/index` - Index a document
- `GET /documents/indexed` - List indexed documents
- `DELETE /documents/indexed/{source}` - Delete indexed document
- `POST /chat/` - Send chat message and get response

## Technologies

- **Next.js 16** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Hooks** - State management
