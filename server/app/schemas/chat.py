# schemas/chat.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    sources: List[str]
    conversation_id: str
    timestamp: Optional[datetime]