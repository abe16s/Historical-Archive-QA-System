"""
Infrastructure layer package.

This package contains low-level adapters and integrations:
- Embedding model initialization
- Vector store (ChromaDB) operations
- Document loading and chunking
- Local file storage helpers
- Low-level RAG engine based on LangChain

Higher-level services should depend on these modules via the
`app.services.*` and `app.core.deps` modules, not import
chromadb, sentence-transformers, etc. directly from routers.
"""


