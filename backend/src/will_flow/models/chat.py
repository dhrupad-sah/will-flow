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
    title: str = "New Chat"  # Title for the thread
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    id: Optional[str] = None


class ChatRequest(BaseModel):
    flow_id: str
    user_email: EmailStr
    message: str
    session_id: Optional[str] = None
    new_thread: bool = False  # Flag to create a new thread


class ChatResponse(BaseModel):
    session_id: str
    response: str
    messages: List[Message]


class ThreadInfo(BaseModel):
    """Info about a chat thread for listing purposes"""
    id: str
    title: str
    flow_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int 