from datetime import datetime
import json
from typing import List, Optional

import httpx
from opensearchpy import OpenSearch

from will_flow.core.config import settings
from will_flow.db.opensearch import opensearch_client
from will_flow.models.chat import ChatRequest, ChatResponse, ChatSession, Message
from will_flow.services.flow_service import FlowService


class ChatService:
    def __init__(self, client: OpenSearch = opensearch_client):
        self.client = client
        self.index = "chat_history"
        self.flow_service = FlowService(client)
    
    async def create_session(self, flow_id: str, user_email: str) -> Optional[ChatSession]:
        # Check if flow exists
        flow = await self.flow_service.get_flow(flow_id)
        if not flow:
            return None
        
        # Create session
        session = ChatSession(
            flow_id=flow_id,
            user_email=user_email,
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
            
            # Return updated session
            return await self.get_session(session_id)
        except Exception as e:
            print(f"Error adding message: {e}")
            return None
    
    async def process_chat(self, chat_request: ChatRequest) -> ChatResponse:
        # Get or create session
        session = None
        if chat_request.session_id:
            session = await self.get_session(chat_request.session_id)
        
        if not session:
            session = await self.create_session(chat_request.flow_id, chat_request.user_email)
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