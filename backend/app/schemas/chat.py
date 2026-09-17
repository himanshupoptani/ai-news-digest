from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class ChatTurnRequest(BaseModel):
    """Incoming user chat message."""
    session_id: Optional[int] = Field(default=None, description="Existing session ID, or None to create a new session")
    message: str = Field(..., min_length=1, description="User question, e.g., 'What happened with Nvidia earnings?'")

class ChatMessageDTO(BaseModel):
    """Standardized representation of a single chat turn."""
    id: int
    role: str  # 'user' or 'assistant'
    content: str
    evidence_strength: Optional[str] = None
    created_at: str

class ChatTurnResponse(BaseModel):
    """Complete response returned to the UI after executing the 14-stage pipeline."""
    session_id: int
    original_query: str
    rewritten_query: str
    role: str = "assistant"
    content: str
    citations: List[Any] = []
    evidence_strength: str
    audit_report: Any = {}
