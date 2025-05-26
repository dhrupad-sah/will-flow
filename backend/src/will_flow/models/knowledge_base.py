from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentInfo(BaseModel):
    """Document information within a knowledge base"""
    doc_id: str
    file_name: str
    file_type: str
    status: str
    upload_time: datetime
    size_bytes: int


class KnowledgeBase(BaseModel):
    """Knowledge base model"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    user_email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    documents: List[DocumentInfo] = []


class KnowledgeBaseCreate(BaseModel):
    """Knowledge base creation model"""
    name: str
    description: Optional[str] = None


class KnowledgeBaseUpdate(BaseModel):
    """Knowledge base update model"""
    name: Optional[str] = None
    description: Optional[str] = None 