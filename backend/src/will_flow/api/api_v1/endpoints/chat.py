from fastapi import APIRouter, Depends, HTTPException

from will_flow.models.chat import ChatRequest, ChatResponse
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


@router.get("/session/{session_id}")
async def get_chat_session(session_id: str):
    """
    Get a chat session by ID.
    """
    session = await chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session 