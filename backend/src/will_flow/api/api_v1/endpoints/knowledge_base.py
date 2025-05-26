from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
import httpx
import datetime
import logging

from will_flow.models.knowledge_base import KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, DocumentInfo
from will_flow.services.kb_service import kb_service
from will_flow.services.ragflow_service import ragflow_service

router = APIRouter()


@router.post("", response_model=KnowledgeBase)
async def create_knowledge_base(
    kb_create: KnowledgeBaseCreate,
    user_email: str = Query(..., description="User email")
):
    """Create a new knowledge base"""
    try:
        # Log the input data for debugging
        logger = logging.getLogger(__name__)
        logger.info(f"Creating knowledge base with data: {kb_create.model_dump()}")
        logger.info(f"User email: {user_email}")
        
        # Create the knowledge base in RAGFlow
        kb = await ragflow_service.create_knowledge_base(user_email, kb_create)
        
        # Save to OpenSearch
        kb = await kb_service.create_kb(kb)
        
        return kb
    except Exception as e:
        # Log the full error details
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create knowledge base: {str(e)}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create knowledge base: {str(e)}"
        )


@router.get("", response_model=List[KnowledgeBase])
async def list_knowledge_bases(
    user_email: str = Query(..., description="User email")
):
    """List knowledge bases for a user"""
    try:
        kbs = await kb_service.list_kbs_by_user(user_email)
        return kbs
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list knowledge bases: {str(e)}"
        )


@router.get("/{kb_id}", response_model=KnowledgeBase)
async def get_knowledge_base(kb_id: str):
    """Get a knowledge base by ID"""
    kb = await kb_service.get_kb(kb_id)
    if not kb:
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge base with ID {kb_id} not found"
        )
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBase)
async def update_knowledge_base(
    kb_id: str,
    kb_update: KnowledgeBaseUpdate
):
    """Update a knowledge base"""
    kb = await kb_service.update_kb(kb_id, kb_update)
    if not kb:
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge base with ID {kb_id} not found"
        )
    return kb


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    """Delete a knowledge base"""
    # Delete from RAGFlow first
    try:
        await ragflow_service.delete_knowledge_base(kb_id)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete knowledge base from RAGFlow: {str(e)}"
        )
    
    # Then delete from OpenSearch
    success = await kb_service.delete_kb(kb_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge base with ID {kb_id} not found"
        )
    
    return {"status": "success", "message": f"Knowledge base {kb_id} deleted"}


@router.post("/{kb_id}/documents", response_model=DocumentInfo)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...)
):
    """Upload a document to a knowledge base"""
    # Check if knowledge base exists
    kb = await kb_service.get_kb(kb_id)
    if not kb:
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge base with ID {kb_id} not found"
        )
    
    try:
        # Upload to RAGFlow
        doc_info = await ragflow_service.upload_document(kb_id, file)
        
        # Update in OpenSearch
        await kb_service.add_document(kb_id, doc_info)
        
        return doc_info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/{kb_id}/documents/{doc_id}", response_model=DocumentInfo)
async def get_document_status(kb_id: str, doc_id: str):
    """Get the status of a document"""
    # Check if knowledge base exists
    kb = await kb_service.get_kb(kb_id)
    if not kb:
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge base with ID {kb_id} not found"
        )
    
    # Find document in KB
    doc_info = None
    for doc in kb.documents:
        if doc.doc_id == doc_id:
            doc_info = doc
            break
    
    if not doc_info:
        raise HTTPException(
            status_code=404,
            detail=f"Document with ID {doc_id} not found in knowledge base {kb_id}"
        )
    
    try:
        # Get status from RAGFlow
        status = await ragflow_service.get_document_status(kb_id, doc_id)
        
        # Update status in OpenSearch if changed
        if status != doc_info.status:
            await kb_service.update_document_status(kb_id, doc_id, status)
            doc_info.status = status
        
        return doc_info
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get document status: {str(e)}"
        )


@router.post("/{kb_id}/chat")
async def chat_with_kb(
    kb_id: str,
    query: str = Form(...),
    session_id: Optional[str] = Form(None),
    user_email: str = Form(...)
):
    """Chat with a knowledge base"""
    # Check if knowledge base exists
    kb = await kb_service.get_kb(kb_id)
    if not kb:
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge base with ID {kb_id} not found"
        )
    
    try:
        # Get history if session_id is provided
        history = []
        # TODO: Implement history retrieval from chat service if needed
        
        # Chat with RAGFlow
        response = await ragflow_service.chat_with_knowledge_base(kb_id, query, history)
        
        # TODO: Save conversation to chat history if needed
        
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to chat with knowledge base: {str(e)}"
        )


@router.get("/debug/connection")
async def test_ragflow_connection():
    """Test the connection to RAGFlow"""
    try:
        # Try to list knowledge bases as a simple test
        kb_list = await ragflow_service.list_knowledge_bases()
        
        # Also try a direct HTTP request to the API root to get service info
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{ragflow_service.api_url}/api/v1",
                headers={"Authorization": f"Bearer {ragflow_service.api_key}"}
            )
            
            service_info = {}
            if response.status_code == 200:
                service_info = response.json()
            
            # Return diagnostics
            return {
                "status": "connected",
                "api_url": ragflow_service.api_url,
                "knowledge_bases_count": len(kb_list),
                "knowledge_bases": kb_list,
                "service_info": service_info,
                "connection_time": datetime.datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "api_url": ragflow_service.api_url,
            "error": str(e),
            "error_type": type(e).__name__,
            "connection_time": datetime.datetime.utcnow().isoformat()
        } 