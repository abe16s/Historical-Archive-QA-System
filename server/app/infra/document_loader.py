from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from io import BytesIO
import re

try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    fitz = None


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
    if not text or not text.strip():
        return None
    
    # Look for common page number patterns throughout the text
    # Patterns: "Page 52", "52", "p. 52", "p52", "- 52 -", "52 of 100", etc.
    lines = text.strip().split('\n')
    
    # More comprehensive patterns
    patterns = [
        r'(?i)page\s+(\d+)',           # "Page 52" or "page 52"
        r'(?i)p\.?\s*(\d+)',          # "p. 52" or "p52"
        r'(?i)pg\.?\s*(\d+)',          # "pg. 52" or "pg52"
        r'^(\d+)$',                    # Just a number on its own line
        r'^(\d+)\s*$',                 # Number with whitespace
        r'^(\d+)\s+of\s+\d+',         # "52 of 100"
        r'^-\s*(\d+)\s*-',             # "- 52 -"
        r'^\s*(\d+)\s*$',              # Number with surrounding whitespace
        r'\((\d+)\)',                  # "(52)" in parentheses
        r'\[(\d+)\]',                  # "[52]" in brackets
    ]
    
    # Check first 10 lines (header area) - more thorough
    for line in lines[:10]:
        line_clean = line.strip()
        for pattern in patterns:
            match = re.search(pattern, line_clean)
            if match:
                try:
                    page_num = int(match.group(1))
                    # More reasonable range check
                    if 1 <= page_num <= 10000:
                        return page_num
                except (ValueError, IndexError):
                    continue
    
    # Check last 10 lines (footer area) - more thorough
    for line in lines[-10:]:
        line_clean = line.strip()
        for pattern in patterns:
            match = re.search(pattern, line_clean)
            if match:
                try:
                    page_num = int(match.group(1))
                    if 1 <= page_num <= 10000:
                        return page_num
                except (ValueError, IndexError):
                    continue
    
    return None


def extract_text_from_pdf(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Extract text content from a PDF file with page information using PyMuPDF.
    
    PyMuPDF provides better page number extraction capabilities than PyPDF2.
    """
    if not PDF_SUPPORT or fitz is None:
        raise ImportError("PyMuPDF (pymupdf) is not installed. Install it with: pip install pymupdf")

    try:
        # Open PDF from bytes
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        if pdf_document.is_encrypted:
            # Try to decrypt with empty password (many PDFs have empty password)
            if not pdf_document.authenticate(""):
                raise ValueError("PDF is encrypted and cannot be processed. Provide an unencrypted PDF.")

        page_texts: List[Dict[str, Any]] = []
        
        # Track extracted page numbers to help infer offset for pages without explicit numbers
        extracted_page_numbers = []
        
        for pdf_page_idx in range(len(pdf_document)):
            try:
                page = pdf_document[pdf_page_idx]
                page_text = page.get_text() or ""
                
                if page_text.strip():
                    # Try to extract actual page number from text (improved function)
                    extracted_page_num = _extract_page_number_from_text(page_text)
                    
                    if extracted_page_num:
                        extracted_page_numbers.append((pdf_page_idx, extracted_page_num))
                        page_num = extracted_page_num
                    else:
                        # Use PDF page index (0-based, so add 1 for 1-based numbering)
                        # This is a fallback - will be improved if we find page numbers later
                        page_num = pdf_page_idx + 1
                    
                    page_texts.append({
                        "text": page_text,
                        "page": page_num
                    })
            except Exception as exc:
                print(f"Warning: Could not extract text from page {pdf_page_idx + 1}: {exc}")
                continue

        pdf_document.close()

        if not page_texts:
            raise ValueError("No text content could be extracted from the PDF (possibly image-only).")

        # Post-processing: If we found some extracted page numbers, try to infer offset
        # for pages that are still using PDF indices
        if extracted_page_numbers and len(extracted_page_numbers) > 0:
            # Calculate average offset between PDF index (0-based) and extracted page number
            offsets = [extracted_num - (pdf_idx + 1) for pdf_idx, extracted_num in extracted_page_numbers]
            avg_offset = sum(offsets) / len(offsets) if offsets else 0
            
            # If there's a consistent offset (within reasonable range), apply it to pages without extracted numbers
            if abs(avg_offset) > 0.5 and abs(avg_offset) < 20:  # Reasonable offset range
                offset = int(round(avg_offset))
                # Apply offset to pages that are still using PDF index fallback
                # (identified by checking if page number matches sequential PDF index)
                for idx, page_data in enumerate(page_texts):
                    pdf_index_plus_one = idx + 1
                    # If the stored page number matches the PDF index, it's likely a fallback
                    if page_data["page"] == pdf_index_plus_one:
                        # Apply the offset
                        corrected_page = page_data["page"] + offset
                        if corrected_page > 0:  # Ensure positive page number
                            page_data["page"] = corrected_page

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


