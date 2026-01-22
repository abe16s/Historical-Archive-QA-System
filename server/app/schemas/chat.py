from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SourceInfo(BaseModel):
    """Information about a source citation."""
    source: str
    page: Optional[int] = None
    display_text: str
    url: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[SourceInfo]
    conversation_id: str
    timestamp: Optional[datetime]