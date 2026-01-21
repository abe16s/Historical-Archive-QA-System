from typing import List, Dict, Optional
from datetime import datetime, timezone
from uuid import uuid4
from collections import defaultdict

from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationService:
    """In-memory service for storing conversation history."""
    
    def __init__(self):
        self._conversations: Dict[str, List[Message]] = defaultdict(list)
    
    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid4())
        self._conversations[conversation_id] = []
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[List[Message]]:
        """Get conversation history by ID."""
        return self._conversations.get(conversation_id)
    
    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to a conversation."""
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []
        self._conversations[conversation_id].append(Message(role=role, content=content))
    
    def get_recent_messages(self, conversation_id: str, limit: int = 10) -> List[Message]:
        """Get the most recent messages from a conversation."""
        messages = self.get_conversation(conversation_id)
        if not messages:
            return []
        return messages[-limit:]
    
    def clear_conversation(self, conversation_id: str) -> None:
        """Clear all messages from a conversation."""
        if conversation_id in self._conversations:
            self._conversations[conversation_id] = []
