"""
Document loading and processing utilities.

Responsible for:
- Loading text files from disk
- Splitting text into chunks with overlap
- Extracting text from PDFs
- Validating uploaded files
"""

from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from io import BytesIO

try:
    from PyPDF2 import PdfReader

    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


def load_text_file(file_path: str) -> str:
    """Load a text file and return its content as a string."""
    return Path(file_path).read_text(encoding="utf-8")


def load_documents_from_directory(directory: str) -> List[Dict[str, str]]:
    """
    Load all .txt files from a directory.

    Returns a list of dicts with 'content' and 'metadata'.
    """
    documents: List[Dict[str, str]] = []
    for file in Path(directory).glob("*.txt"):
        documents.append(
            {
                "content": load_text_file(str(file)),
                "metadata": {"source": str(file.name)},
            }
        )
    return documents


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Split text into overlapping character-based chunks.
    """
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += max(chunk_size - chunk_overlap, 1)
    return chunks


def process_documents(
    directory: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Dict[str, Any]]:
    """
    Load and process all documents from a directory into chunks with metadata.
    """
    chunks: List[Dict[str, Any]] = []
    docs = load_documents_from_directory(directory)
    for doc in docs:
        doc_chunks = split_text_into_chunks(doc["content"], chunk_size, chunk_overlap)
        for idx, chunk in enumerate(doc_chunks):
            chunks.append(
                {
                    "content": chunk,
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": idx,
                    },
                }
            )
    return chunks


def process_uploaded_file(
    file_content: str,
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Dict[str, Any]]:
    """
    Process an uploaded file's text content into chunks with metadata.
    """
    chunks: List[Dict[str, Any]] = []
    doc_chunks = split_text_into_chunks(file_content, chunk_size, chunk_overlap)
    for idx, chunk in enumerate(doc_chunks):
        chunks.append(
            {
                "content": chunk,
                "metadata": {
                    "source": filename,
                    "chunk_index": idx,
                    "upload_type": "file_upload",
                },
            }
        )
    return chunks


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text content from a PDF file.
    Raises ValueError if no text can be extracted.
    """
    if not PDF_SUPPORT:
        raise ImportError("PyPDF2 is not installed. Install it with: pip install PyPDF2")

    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        if reader.is_encrypted:
            raise ValueError("PDF is encrypted and cannot be processed. Provide an unencrypted PDF.")

        text_chunks: List[str] = []
        for page_num, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    text_chunks.append(page_text)
            except Exception as exc:
                print(f"Warning: Could not extract text from page {page_num + 1}: {exc}")
                continue

        if not text_chunks:
            raise ValueError("No text content could be extracted from the PDF (possibly image-only).")

        return "\n\n".join(text_chunks)
    except Exception as exc:
        raise ValueError(f"Error reading PDF: {exc}")


def validate_file_upload(
    filename: Optional[str],
    file_size: int,
    max_size_mb: int = 10,
) -> Tuple[bool, Optional[str]]:
    """
    Validate an uploaded file (name, extension, size).
    """
    if not filename:
        return False, "Filename is required"

    allowed_extensions = {".txt", ".pdf", ".docx", ".md"}
    file_ext = Path(filename).suffix.lower()
    if file_ext not in allowed_extensions:
        return False, f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"

    max_bytes = max_size_mb * 1024 * 1024
    if file_size > max_bytes:
        return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"

    if file_size == 0:
        return False, "File is empty"

    return True, None


