# Historical Archive QA System

A RAG-based question-answering system for historical documents using Google Gemini, ChromaDB, and FastAPI.

## Features

1. **Document Upload** - Upload documents (PDF, TXT, MD formats) to local storage
2. **Document Listing** - List all uploaded files and indexed documents
3. **Document Indexing** - Process and index documents into the vector database
4. **Chat/QA** - Ask questions and get answers with source citations

## Setup

### 1. Create Virtual Environment (Recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
cd server
pip install --upgrade pip setuptools
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
VECTOR_DB_PATH=./vector_db
UPLOAD_DIR=./uploads
```

Optional configuration:
```env
GEMINI_MODEL=gemini-2.5-flash-lite
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=7
LLM_TEMPERATURE=0.7
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Run the Server

From the `server` directory:

```bash
python -m app.main
```

Or using uvicorn directly:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Documents

#### 1. Upload Document
**POST** `/documents/upload`

Upload a document (PDF, TXT, MD) to local storage without indexing.

**Request:** Multipart form data with `file` field

**Response:**
```json
{
  "message": "File uploaded successfully",
  "filename": "document.pdf",
  "chunks_count": null,
  "file_path": "document-abc123.pdf"
}
```

#### 2. List Uploaded Documents
**GET** `/documents/list`

Get a list of all uploaded documents.

**Response:**
```json
[
  {
    "key": "document-abc123.pdf",
    "size": 12345,
    "last_modified": "2024-01-01T12:00:00",
    "original_filename": "document.pdf",
    "signed_url": null
  }
]
```

#### 3. Index Document
**POST** `/documents/index`

Index an uploaded document. Provide either `file_path` OR `filename`, but not both.

**Request Body:**
```json
{
  "file_path": "document-abc123.pdf"
}
```
or
```json
{
  "filename": "document.pdf"
}
```

**Response:**
```json
{
  "message": "Successfully indexed 42 document chunks",
  "filename": "document.pdf",
  "chunks_count": 42,
  "file_path": "document-abc123.pdf"
}
```

#### 4. List Indexed Documents
**GET** `/documents/indexed`

Get a list of all indexed documents with chunk counts.

**Response:**
```json
[
  {
    "source": "document.pdf",
    "chunks_count": 42,
    "last_indexed_at": "2024-01-01T12:00:00"
  }
]
```

#### 5. Delete Indexed Document
**DELETE** `/documents/indexed/{source}`

Remove all indexed chunks for a document source.

**Response:**
```json
{
  "source": "document.pdf",
  "deleted_chunks": 42
}
```

### Chat

#### Ask Questions
**POST** `/chat/`

Ask a question about the indexed documents.

**Request Body:**
```json
{
  "message": "What was discussed in the document?"
}
```

**Response:**
```json
{
  "response": "The document discussed...",
  "sources": ["document.pdf"],
  "conversation_id": "uuid-here",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Workflow

1. **Upload** a document using `POST /documents/upload`
2. **Index** the document using `POST /documents/index` (provide `file_path` or `filename`)
3. **Ask questions** using `POST /chat/` to get answers with source citations

## Architecture

- **Document Processing**: PyPDF2 for PDF text extraction, native support for TXT/MD
- **Embeddings**: SentenceTransformer (all-MiniLM-L6-v2) - local, no API calls, no quota limits
- **Vector Store**: ChromaDB for similarity search
- **LLM**: Google Gemini via LangChain for answer generation
- **Storage**: Local filesystem for document storage
- **API**: FastAPI with automatic OpenAPI documentation

## Project Structure

```
Historical-Archive-QA-System/
├── server/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── chat.py            # Chat endpoints
│   │   │       └── documents.py       # Document endpoints
│   │   ├── core/
│   │   │   ├── config.py              # Configuration management
│   │   │   └── deps.py                # Dependency injection
│   │   ├── infra/
│   │   │   ├── document_loader.py     # Document processing
│   │   │   ├── embeddings.py          # Embedding generation
│   │   │   ├── rag_engine.py          # RAG pipeline
│   │   │   └── vector_store.py        # ChromaDB operations
│   │   ├── schemas/
│   │   │   ├── chat.py                # Chat request/response models
│   │   │   └── documents.py           # Document request/response models
│   │   └── services/
│   │       ├── document_service.py    # Document management service
│   │       ├── rag_service.py         # RAG pipeline service
│   │       └── storage_service.py      # Local file storage service
│   ├── requirements.txt
│   ├── uploads/                       # Uploaded documents (local storage)
│   └── vector_db/                     # ChromaDB database
├── README.md
└── .env
```

## Configuration

Edit `server/app/core/config.py` or set environment variables to adjust:
- Chunk size and overlap for text splitting (`CHUNK_SIZE`, `CHUNK_OVERLAP`)
- Number of retrieved chunks (`TOP_K_RETRIEVAL`)
- LLM model selection (`GEMINI_MODEL`, `LLM_PROVIDER`)
- Embedding model (`EMBEDDING_MODEL`)
- Server host and port (`API_HOST`, `API_PORT`)
- Upload directory (`UPLOAD_DIR`)
- Vector database path (`VECTOR_DB_PATH`)

## RAG Implementation Details

The RAG pipeline follows best practices:

1. **Document Processing**: Documents are split into overlapping chunks with metadata (source, page number)
2. **Embedding Generation**: Uses SentenceTransformer (local) for document and query embeddings
3. **Vector Storage**: ChromaDB with cosine similarity for semantic search
4. **Context Retrieval**: Top-K most relevant chunks retrieved based on query similarity
5. **Answer Generation**: Gemini LLM generates answers with strict instructions to cite sources
6. **Source Citation**: Automatic extraction of source documents and page numbers from context

## Error Handling

The system includes comprehensive error handling:
- Proper HTTP status codes
- Detailed error messages
- Validation for file uploads and indexing requests
