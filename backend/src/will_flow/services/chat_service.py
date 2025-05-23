from datetime import datetime
import json
from typing import List, Optional

import httpx
from opensearchpy import OpenSearch

from will_flow.core.config import settings
from will_flow.db.opensearch import opensearch_client
from will_flow.models.chat import ChatRequest, ChatResponse, ChatSession, Message, ThreadInfo
from will_flow.services.flow_service import FlowService


class ChatService:
    def __init__(self, client: OpenSearch = opensearch_client):
        self.client = client
        self.index = "chat_history"
        self.flow_service = FlowService(client)
    
    async def create_session(self, flow_id: str, user_email: str, title: str = "New Chat") -> Optional[ChatSession]:
        # Check if flow exists
        flow = await self.flow_service.get_flow(flow_id)
        if not flow:
            return None
        
        # Create session
        session = ChatSession(
            flow_id=flow_id,
            user_email=user_email,
            title=title,
            messages=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session_dict = session.model_dump()
        # Convert datetime objects to strings
        for field in ["created_at", "updated_at"]:
            session_dict[field] = session_dict[field].isoformat()
        
        # Convert nested objects
        session_dict["messages"] = [msg.model_dump() for msg in session.messages]
        for msg in session_dict["messages"]:
            if "timestamp" in msg:
                msg["timestamp"] = msg["timestamp"].isoformat()
        
        result = self.client.index(
            index=self.index,
            body=session_dict,
            refresh=True
        )
        
        session_dict["id"] = result["_id"]
        return ChatSession(**session_dict)
    
    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        try:
            result = self.client.get(
                index=self.index,
                id=session_id
            )
            
            session_data = result["_source"]
            session_data["id"] = result["_id"]
            
            # Convert message objects
            messages = []
            for msg_data in session_data.get("messages", []):
                messages.append(Message(**msg_data))
            
            session_data["messages"] = messages
            
            return ChatSession(**session_data)
        except Exception as e:
            print(f"Error fetching chat session: {e}")
            return None
    
    async def update_session_title(self, session_id: str, title: str) -> Optional[ChatSession]:
        """Update the title of a chat session (thread)"""
        try:
            self.client.update(
                index=self.index,
                id=session_id,
                body={
                    "doc": {
                        "title": title,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                },
                refresh=True
            )
            
            return await self.get_session(session_id)
        except Exception as e:
            print(f"Error updating session title: {e}")
            return None
    
    async def list_user_threads(self, user_email: str, flow_id: Optional[str] = None) -> List[ThreadInfo]:
        """List all threads for a user, optionally filtered by flow"""
        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"user_email": user_email}}
                    ]
                }
            }
            
            if flow_id:
                query["bool"]["must"].append({"term": {"flow_id": flow_id}})
            
            result = self.client.search(
                index=self.index,
                body={
                    "query": query,
                    "sort": [
                        {"updated_at": {"order": "desc"}}
                    ]
                }
            )
            
            threads = []
            for hit in result["hits"]["hits"]:
                source = hit["_source"]
                message_count = len(source.get("messages", []))
                
                # Parse datetime strings back to datetime objects
                created_at = datetime.fromisoformat(source.get("created_at"))
                updated_at = datetime.fromisoformat(source.get("updated_at"))
                
                thread = ThreadInfo(
                    id=hit["_id"],
                    title=source.get("title", "Untitled Chat"),
                    flow_id=source.get("flow_id"),
                    created_at=created_at,
                    updated_at=updated_at,
                    message_count=message_count
                )
                threads.append(thread)
            
            return threads
        except Exception as e:
            print(f"Error listing user threads: {e}")
            return []
    
    async def add_message(self, session_id: str, message: Message) -> Optional[ChatSession]:
        try:
            # Get existing session
            session = await self.get_session(session_id)
            if not session:
                return None
            
            # Add message
            message_dict = message.model_dump()
            if "timestamp" in message_dict:
                message_dict["timestamp"] = message_dict["timestamp"].isoformat()
            
            # Update session
            self.client.update(
                index=self.index,
                id=session_id,
                body={
                    "script": {
                        "source": "ctx._source.messages.add(params.message); ctx._source.updated_at = params.updated_at",
                        "lang": "painless",
                        "params": {
                            "message": message_dict,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                },
                refresh=True
            )
            
            # Auto-name the thread if it's the first message and has default title
            session = await self.get_session(session_id)
            if session.title == "New Chat" and len(session.messages) == 1:
                # Use the first part of the user's message as the title
                first_message = session.messages[0].content
                title = first_message[:30] + "..." if len(first_message) > 30 else first_message
                await self.update_session_title(session_id, title)
                session = await self.get_session(session_id)
            
            return session
        except Exception as e:
            print(f"Error adding message: {e}")
            return None
    
    async def process_chat(self, chat_request: ChatRequest) -> ChatResponse:
        # Get or create session
        session = None
        
        # Check if we should create a new thread
        if chat_request.new_thread:
            session = await self.create_session(
                chat_request.flow_id, 
                chat_request.user_email
            )
        # Use existing thread if session_id is provided
        elif chat_request.session_id:
            session = await self.get_session(chat_request.session_id)
        
        # If no session yet, create a new one
        if not session:
            session = await self.create_session(
                chat_request.flow_id, 
                chat_request.user_email
            )
        
        if not session:
            raise ValueError(f"Flow with ID {chat_request.flow_id} not found")
        
        # Get flow
        flow = await self.flow_service.get_flow(chat_request.flow_id)
        if not flow:
            raise ValueError(f"Flow with ID {chat_request.flow_id} not found")
        
        # Ensure session has an id
        if not hasattr(session, 'id') or not session.id:
            raise ValueError("Chat session is missing an ID")
        
        # Add user message to session
        user_message = Message(role="user", content=chat_request.message)
        session = await self.add_message(session.id, user_message)
        if not session:
            raise ValueError("Failed to add message to chat session")
        
        # Prepare messages for API call
        messages = [{"role": "system", "content": flow.system_prompt}]
        
        # Add conversation history
        for msg in session.messages:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Call OpenRouter API
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": flow.model,
                "messages": messages
            }
            
            response = await client.post(
                f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                print(f"OpenRouter API error: {response.text}")
                raise Exception(f"OpenRouter API error: {response.status_code}")
            
            response_data = response.json()
            assistant_message_content = response_data["choices"][0]["message"]["content"]
        
        # Add assistant message to session
        assistant_message = Message(role="assistant", content=assistant_message_content)
        session = await self.add_message(session.id, assistant_message)
        if not session:
            raise ValueError("Failed to add assistant message to chat session")
        
        # Return response
        return ChatResponse(
            session_id=session.id,
            response=assistant_message_content,
            messages=session.messages
        ) 