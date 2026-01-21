from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from io import BytesIO
import re

try:
    from PyPDF2 import PdfReader
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


def load_text_file(file_path: str) -> str:
    """Load a text file and return its content as a string."""
    return Path(file_path).read_text(encoding="utf-8")


def load_documents_from_directory(directory: str) -> List[Dict[str, str]]:
    """Load all .txt files from a directory."""
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
    """Split text into overlapping character-based chunks."""
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
    """Load and process all documents from a directory into chunks with metadata."""
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
    file_content: str | List[Dict[str, Any]],
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Dict[str, Any]]:
    """Process an uploaded file's text content into chunks with metadata."""
    chunks: List[Dict[str, Any]] = []
    
    if isinstance(file_content, list):
        for page_data in file_content:
            page_text = page_data.get("text", "")
            page_num = page_data.get("page", 1)
            page_chunks = split_text_into_chunks(page_text, chunk_size, chunk_overlap)
            for idx, chunk in enumerate(page_chunks):
                chunks.append(
                    {
                        "content": chunk,
                        "metadata": {
                            "source": filename,
                            "page": page_num,
                            "chunk_index": idx,
                            "upload_type": "file_upload",
                        },
                    }
                )
    else:
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


def _extract_page_number_from_text(text: str) -> Optional[int]:
    """Try to extract page number from text (usually in headers/footers)."""
    # Look for common page number patterns at the start or end of text
    # Patterns: "Page 52", "52", "p. 52", "p52", etc.
    lines = text.strip().split('\n')
    
    # Check first few lines (header area)
    for line in lines[:5]:
        # Look for "Page X" or "p. X" or "pX" patterns
        patterns = [
            r'(?i)page\s+(\d+)',
            r'(?i)p\.?\s*(\d+)',
            r'^(\d+)$',  # Just a number on its own line
        ]
        for pattern in patterns:
            match = re.search(pattern, line.strip())
            if match:
                try:
                    page_num = int(match.group(1))
                    if 1 <= page_num <= 10000:  # Reasonable page number range
                        return page_num
                except ValueError:
                    continue
    
    # Check last few lines (footer area)
    for line in lines[-5:]:
        for pattern in patterns:
            match = re.search(pattern, line.strip())
            if match:
                try:
                    page_num = int(match.group(1))
                    if 1 <= page_num <= 10000:
                        return page_num
                except ValueError:
                    continue
    
    return None


def extract_text_from_pdf(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """Extract text content from a PDF file with page information."""
    if not PDF_SUPPORT:
        raise ImportError("PyPDF2 is not installed. Install it with: pip install PyPDF2")

    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        if reader.is_encrypted:
            raise ValueError("PDF is encrypted and cannot be processed. Provide an unencrypted PDF.")

        page_texts: List[Dict[str, Any]] = []
        for pdf_page_idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    # Try to extract actual page number from text
                    extracted_page_num = _extract_page_number_from_text(page_text)
                    
                    # Use extracted page number if found, otherwise fall back to PDF index
                    page_num = extracted_page_num if extracted_page_num else pdf_page_idx
                    
                    page_texts.append({
                        "text": page_text,
                        "page": page_num
                    })
            except Exception as exc:
                print(f"Warning: Could not extract text from page {pdf_page_idx}: {exc}")
                continue

        if not page_texts:
            raise ValueError("No text content could be extracted from the PDF (possibly image-only).")

        return page_texts
    except Exception as exc:
        raise ValueError(f"Error reading PDF: {exc}")


def validate_file_upload(
    filename: Optional[str],
    file_size: int,
    max_size_mb: int = 10,
) -> Tuple[bool, Optional[str]]:
    """Validate an uploaded file (name, extension, size)."""
    if not filename:
        return False, "Filename is required"

    allowed_extensions = {".txt", ".pdf", ".docx", ".md"}
    file_ext = Path(filename).suffix.lower()
    if file_ext not in allowed_extensions:
        return False, f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"

    max_bytes = max_size_mb * 1024 * 1024 * 1024
    if file_size > max_bytes:
        return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"

    if file_size == 0:
        return False, "File is empty"

    return True, None


