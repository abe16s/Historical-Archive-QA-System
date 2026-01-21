from typing import List, Dict, Optional, Tuple
from pathlib import Path
import os
import re
import uuid
from datetime import datetime

from app.core.config import settings


class StorageService:
    """Service for local file storage operations."""

    def __init__(self) -> None:
        self._upload_dir = Path(settings.UPLOAD_DIR)
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    @property
    def upload_dir(self) -> Path:
        return self._upload_dir

    def upload_file_bytes(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """Upload a file to local storage and return its file path."""
        base_name = os.path.basename(filename)
        name_without_ext, ext = os.path.splitext(base_name)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", name_without_ext) or "file"
        unique_filename = f"{safe_name}-{uuid.uuid4().hex}{ext}"
        file_path = self._upload_dir / unique_filename

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        metadata_file = file_path.with_suffix(file_path.suffix + ".meta")
        with open(metadata_file, "w", encoding="utf-8") as f:
            f.write(f"original_filename={filename}\n")
            f.write(f"content_type={content_type}\n")

        return str(file_path.relative_to(self._upload_dir))

    def list_files(self) -> List[Dict[str, Optional[str]]]:
        """List all files in the upload directory."""
        files: List[Dict[str, Optional[str]]] = []

        for file_path in self._upload_dir.glob("*"):
            if file_path.is_dir() or file_path.suffix == ".meta":
                continue

            stat = file_path.stat()
            size = stat.st_size
            last_modified = datetime.fromtimestamp(stat.st_mtime)

            original_filename: Optional[str] = None
            metadata_file = file_path.with_suffix(file_path.suffix + ".meta")
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("original_filename="):
                                original_filename = line.split("=", 1)[1].strip()
                                break
                except Exception:
                    pass

            if not original_filename:
                original_filename = file_path.name

            key = str(file_path.relative_to(self._upload_dir))

            files.append(
                {
                    "key": key,
                    "size": str(size),
                    "last_modified": last_modified.isoformat(),
                    "original_filename": original_filename,
                    "signed_url": None,
                }
            )

        return files

    def get_file_bytes(self, file_key: str) -> Tuple[bytes, Optional[str], Dict[str, str]]:
        """Read a file from local storage and return its bytes, content-type and metadata."""
        file_path = self._upload_dir / file_key
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_key}")

        with open(file_path, "rb") as f:
            body = f.read()

        content_type: Optional[str] = None
        metadata: Dict[str, str] = {}
        metadata_file = file_path.with_suffix(file_path.suffix + ".meta")
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            key, value = line.strip().split("=", 1)
                            metadata[key] = value
                            if key == "content_type":
                                content_type = value
            except Exception:
                pass

        return body, content_type, metadata
