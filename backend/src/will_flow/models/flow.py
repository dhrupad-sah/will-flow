from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class FlowBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    model: str


class FlowCreate(FlowBase):
    creator_email: EmailStr


class FlowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model: Optional[str] = None


class FlowInDB(FlowBase):
    id: str
    creator_email: EmailStr
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Flow(FlowInDB):
    pass 