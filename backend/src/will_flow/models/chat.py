from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    flow_id: str
    user_email: EmailStr
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    id: Optional[str] = None


class ChatRequest(BaseModel):
    flow_id: str
    user_email: EmailStr
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    messages: List[Message] 