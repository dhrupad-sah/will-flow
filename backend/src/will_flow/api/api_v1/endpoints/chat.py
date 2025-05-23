from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from will_flow.models.chat import ChatRequest, ChatResponse, ChatSession, ThreadInfo
from will_flow.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/", response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    """
    Process a chat message and return a response.
    """
    try:
        return await chat_service.process_chat(chat_request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing error: {str(e)}")


@router.get("/session/{session_id}", response_model=ChatSession)
async def get_chat_session(session_id: str):
    """
    Get a chat session by ID.
    """
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


@router.get("/threads", response_model=List[ThreadInfo])
async def list_threads(user_email: str, flow_id: Optional[str] = None):
    """
    List all threads for a user, optionally filtered by flow ID.
    """
    try:
        threads = await chat_service.list_user_threads(user_email, flow_id)
        return threads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing threads: {str(e)}")


@router.put("/session/{session_id}/title", response_model=ChatSession)
async def update_thread_title(session_id: str, title: str):
    """
    Update the title of a chat thread.
    """
    try:
        session = await chat_service.update_session_title(session_id, title)
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating thread title: {str(e)}")


@router.delete("/session/{session_id}")
async def delete_thread(session_id: str):
    """
    Delete a chat thread by ID.
    """
    try:
        success = await chat_service.delete_thread(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Chat thread not found")
        return {"success": True, "message": "Thread deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting thread: {str(e)}") 