import os
import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from fastapi import UploadFile

from will_flow.models.knowledge_base import KnowledgeBase, KnowledgeBaseCreate, DocumentInfo
from will_flow.core.config import settings

# Import RAGFlow SDK if available, otherwise use direct API calls
try:
    from ragflow_sdk import RAGFlow as RAGFlowSDK
    USE_SDK = True
except ImportError:
    USE_SDK = False


class RAGFlowService:
    """Service for interacting with RAGFlow API"""

    def __init__(self):
        self.api_url = "http://10.147.19.152:8080"
        self.api_key = "ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm"
        self.logger = logging.getLogger(__name__)
        
        # Initialize SDK client if available
        if USE_SDK:
            self.client = RAGFlowSDK(
                api_key=self.api_key,
                base_url=self.api_url
            )
            self.logger.info("Using RAGFlow SDK for API interactions")
        else:
            self.client = None
            self.logger.warning("RAGFlow SDK not available, using direct API calls")

    async def create_knowledge_base(self, user_email: str, kb_create: KnowledgeBaseCreate) -> KnowledgeBase:
        """Create a new knowledge base in RAGFlow"""
        try:
            if USE_SDK:
                try:
                    # First attempt: Use SDK but with minimal parameters to avoid issues
                    self.logger.info(f"Creating knowledge base using SDK with parameters: name={kb_create.name}")
                    
                    # Only pass the required name parameter to prevent errors with optional fields
                    dataset = self.client.create_dataset(
                        name=kb_create.name
                    )
                    
                    # Create a new knowledge base record from SDK response
                    kb = KnowledgeBase(
                        id=dataset.id,
                        name=kb_create.name,
                        description=kb_create.description,
                        user_email=user_email,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        documents=[]
                    )
                    
                    self.logger.info(f"Knowledge base created successfully using SDK: {kb.id}")
                    return kb
                    
                except Exception as sdk_error:
                    # Log SDK error and fall back to direct API
                    self.logger.warning(f"SDK method failed, falling back to direct API: {str(sdk_error)}")
                    # Continue to direct API method
            
            # Use direct API call (either as fallback or primary method)
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Use the correct endpoint from documentation
                endpoint = f"{self.api_url}/api/v1/datasets"
                
                # Only include required name field to prevent errors
                payload = {
                    "name": kb_create.name
                }
                
                # Add optional description if provided
                if kb_create.description:
                    payload["description"] = kb_create.description
                
                # Log the payload for debugging
                self.logger.info(f"Creating knowledge base with payload: {payload}")
                
                try:
                    self.logger.info(f"Attempting to create knowledge base at: {endpoint}")
                    response = await client.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json=payload
                    )
                    
                    if response.status_code != 200:
                        error_msg = f"Failed to create knowledge base: {response.text}"
                        self.logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    result = response.json()
                    self.logger.info(f"Knowledge base created successfully: {result}")
                    
                    # Extract dataset ID from response which could be in different formats
                    kb_id = None
                    if isinstance(result, dict):
                        if "data" in result and "id" in result["data"]:
                            # Standard response format: {"code": 0, "data": {"id": "..."}}
                            kb_id = result["data"]["id"]
                        elif "id" in result:
                            # Direct id in response
                            kb_id = result["id"]
                    
                    if not kb_id:
                        raise Exception(f"No ID returned in response: {result}")
                    
                    # Create a new knowledge base record
                    kb = KnowledgeBase(
                        id=kb_id,
                        name=kb_create.name,
                        description=kb_create.description,
                        user_email=user_email,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        documents=[]
                    )
                    
                    return kb
                except Exception as e:
                    self.logger.error(f"Failed to create knowledge base: {str(e)}")
                    raise Exception(f"Failed to create knowledge base: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error creating knowledge base: {str(e)}")
            raise Exception(f"Failed to create knowledge base: {str(e)}")

    async def upload_document(self, kb_id: str, file: UploadFile) -> DocumentInfo:
        """Upload a document to a knowledge base"""
        temp_file_path = f"/tmp/{uuid.uuid4()}_{file.filename}"
        try:
            # Save the uploaded file temporarily
            with open(temp_file_path, "wb") as temp_file:
                content = await file.read()
                temp_file.write(content)
            
            if USE_SDK:
                try:
                    # Get the dataset (knowledge base) from RAGFlow
                    datasets = self.client.list_datasets(id=kb_id)
                    if not datasets:
                        raise Exception(f"Knowledge base with ID {kb_id} not found")
                    
                    dataset = datasets[0]
                    
                    # Read file content for SDK upload
                    with open(temp_file_path, "rb") as f:
                        file_content = f.read()
                    
                    # Use SDK to upload document - follows the correct pattern from docs
                    document_list = [{
                        "display_name": file.filename,
                        "blob": file_content
                    }]
                    
                    self.logger.info(f"Uploading document using SDK to KB {kb_id}: {file.filename}")
                    
                    # Upload documents using SDK method
                    upload_result = dataset.upload_documents(document_list)
                    self.logger.info(f"SDK upload result: {upload_result}")
                    
                    # List documents to get the uploaded one
                    docs = dataset.list_documents()
                    
                    # Find the newly uploaded document (most recent one)
                    if docs:
                        # Get document that matches our filename
                        matching_docs = [doc for doc in docs if hasattr(doc, 'name') and doc.name == file.filename]
                        if matching_docs:
                            doc = matching_docs[0]
                            doc_info = DocumentInfo(
                                doc_id=doc.id,
                                file_name=file.filename,
                                file_type=file.content_type,
                                status="processing",  # Default status
                                upload_time=datetime.utcnow(),
                                size_bytes=os.path.getsize(temp_file_path)
                            )
                            self.logger.info(f"Document uploaded successfully using SDK: {doc_info.doc_id}")
                            return doc_info
                    
                    # If we couldn't find the document, create a placeholder
                    doc_id = str(uuid.uuid4())
                    doc_info = DocumentInfo(
                        doc_id=doc_id,
                        file_name=file.filename,
                        file_type=file.content_type,
                        status="processing",
                        upload_time=datetime.utcnow(),
                        size_bytes=os.path.getsize(temp_file_path)
                    )
                    
                    return doc_info
                    
                except Exception as sdk_error:
                    # Log SDK error and fall back to direct API
                    self.logger.warning(f"SDK upload method failed, falling back to direct API: {str(sdk_error)}")
                    # Continue to direct API method
            
            # Fall back to direct API call
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Use the correct endpoint from documentation
                endpoint = f"{self.api_url}/api/v1/datasets/{kb_id}/documents"
                
                with open(temp_file_path, "rb") as f:
                    # RAGFlow expects a specific file field name: "file"
                    files = {"file": (file.filename, f, file.content_type)}
                    
                    # Log request details for debugging
                    self.logger.info(f"Uploading file to {endpoint}")
                    
                    response = await client.post(
                        endpoint,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        files=files
                    )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to upload document: {response.text}")
                    # Create document info with failed status
                    doc_id = str(uuid.uuid4())
                    doc_info = DocumentInfo(
                        doc_id=doc_id,
                        file_name=file.filename,
                        file_type=file.content_type,
                        status="failed",
                        upload_time=datetime.utcnow(),
                        size_bytes=os.path.getsize(temp_file_path)
                    )
                    return doc_info
                
                result = response.json()
                self.logger.info(f"Document upload success: {result}")
                
                # Extract document ID from the response
                doc_id = None
                if isinstance(result, dict) and "data" in result and len(result["data"]) > 0:
                    doc_id = result["data"][0].get("id")
                
                if not doc_id:
                    # Try other possible formats
                    if isinstance(result, dict):
                        doc_id = result.get("id") or result.get("doc_id")
                
                if not doc_id:
                    doc_id = str(uuid.uuid4())  # Fallback ID if API doesn't return one
                
                # Create document info
                doc_info = DocumentInfo(
                    doc_id=doc_id,
                    file_name=file.filename,
                    file_type=file.content_type,
                    status="processing",
                    upload_time=datetime.utcnow(),
                    size_bytes=os.path.getsize(temp_file_path)
                )
                
                # Start document parsing
                try:
                    parse_payload = {
                        "document_ids": [doc_id]
                    }
                    
                    parse_response = await client.post(
                        f"{self.api_url}/api/v1/datasets/{kb_id}/chunks",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=parse_payload
                    )
                    
                    if parse_response.status_code == 200:
                        self.logger.info(f"Document parsing started successfully: {doc_id}")
                    else:
                        self.logger.warning(f"Document parsing request failed: {parse_response.text}")
                except Exception as parse_error:
                    self.logger.warning(f"Error starting document parsing: {str(parse_error)}")
                
                return doc_info
                
        except Exception as e:
            self.logger.error(f"Exception during file upload: {str(e)}")
            # Create document info with failed status
            doc_id = str(uuid.uuid4())
            doc_info = DocumentInfo(
                doc_id=doc_id,
                file_name=file.filename,
                file_type=file.content_type,
                status="failed",
                upload_time=datetime.utcnow(),
                size_bytes=os.path.getsize(temp_file_path) if os.path.exists(temp_file_path) else 0
            )
            return doc_info
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    async def get_document_status(self, kb_id: str, doc_id: str) -> str:
        """Get the status of a document"""
        try:
            if USE_SDK:
                try:
                    # Get the dataset (knowledge base) from RAGFlow
                    datasets = self.client.list_datasets(id=kb_id)
                    if not datasets:
                        raise Exception(f"Knowledge base with ID {kb_id} not found")
                    
                    dataset = datasets[0]
                    
                    # List documents to find the one we want
                    docs = dataset.list_documents(id=doc_id)
                    if not docs:
                        self.logger.warning(f"Document with ID {doc_id} not found in knowledge base {kb_id}")
                        return "failed"
                    
                    doc = docs[0]
                    
                    # Map RAGFlow document status to our status terms
                    status = doc.run.lower() if hasattr(doc, 'run') else "unknown"
                    
                    if status in ["done", "complete", "completed", "success", "indexed"]:
                        return "ready"
                    elif status in ["running", "processing", "in_progress", "parsing", "indexing", "unstart"]:
                        return "processing"
                    elif status in ["failed", "error", "failure", "cancel", "fail"]:
                        return "failed"
                    else:
                        return "unknown"
                except Exception as sdk_error:
                    # Log SDK error and fall back to direct API
                    self.logger.warning(f"SDK status method failed, falling back to direct API: {str(sdk_error)}")
                    # Continue to direct API method
            
            # Fall back to direct API call
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use the correct endpoint from documentation
                endpoint = f"{self.api_url}/api/v1/datasets/{kb_id}/documents/{doc_id}"
                
                response = await client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to get document status: {response.text}")
                    return "failed"
                
                result = response.json()
                self.logger.info(f"Document status response: {result}")
                
                # Extract status from response
                status = "unknown"
                
                # Handle different response formats
                if isinstance(result, dict):
                    if "data" in result and isinstance(result["data"], dict):
                        # Check for status in data.run
                        data = result["data"]
                        status = data.get("run", "")
                    elif "run" in result:
                        # Direct run status
                        status = result.get("run", "")
                
                # Map RAGFlow status to our status terms
                if isinstance(status, str):
                    status = status.lower()
                    if status in ["done", "complete", "completed", "success", "indexed", "2"]:
                        return "ready"
                    elif status in ["running", "processing", "in_progress", "parsing", "indexing", "unstart", "0", "1"]:
                        return "processing"
                    elif status in ["failed", "error", "failure", "cancel", "fail", "-1"]:
                        return "failed"
                
                return "unknown"
        except Exception as e:
            self.logger.error(f"Error getting document status: {str(e)}")
            return "failed"

    async def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """List all knowledge bases in RAGFlow"""
        try:
            if USE_SDK:
                try:
                    # Use SDK to list datasets (knowledge bases)
                    datasets = self.client.list_datasets()
                    
                    # Convert SDK dataset objects to dictionaries
                    result = []
                    for dataset in datasets:
                        result.append({
                            "id": dataset.id,
                            "name": dataset.name,
                            "description": getattr(dataset, "description", ""),
                            "document_count": getattr(dataset, "document_count", 0),
                            "created_at": getattr(dataset, "create_time", datetime.utcnow().isoformat())
                        })
                    
                    return result
                except Exception as sdk_error:
                    # Log SDK error and fall back to direct API
                    self.logger.warning(f"SDK list method failed, falling back to direct API: {str(sdk_error)}")
                    # Continue to direct API method
            
            # Fall back to direct API call
            async with httpx.AsyncClient() as client:
                # Use the correct endpoint from documentation
                endpoint = f"{self.api_url}/api/v1/datasets"
                
                response = await client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code != 200:
                    self.logger.error(f"Failed to list knowledge bases: {response.text}")
                    raise Exception(f"Failed to list knowledge bases: {response.text}")
                
                result = response.json()
                
                # Handle different response formats
                datasets = []
                if isinstance(result, dict) and "data" in result:
                    datasets = result["data"]
                elif isinstance(result, list):
                    datasets = result
                
                return datasets
        except Exception as e:
            self.logger.error(f"Error listing knowledge bases: {str(e)}")
            raise Exception(f"Failed to list knowledge bases: {str(e)}")

    async def delete_knowledge_base(self, kb_id: str) -> bool:
        """Delete a knowledge base"""
        try:
            if USE_SDK:
                # Use SDK to delete dataset (knowledge base)
                self.client.delete_datasets(ids=[kb_id])
                return True
            else:
                # Fall back to direct API call
                async with httpx.AsyncClient() as client:
                    response = await client.delete(
                        f"{self.api_url}/api/v1/knowledge-bases/{kb_id}",
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    
                    if response.status_code != 200:
                        self.logger.error(f"Failed to delete knowledge base: {response.text}")
                        raise Exception(f"Failed to delete knowledge base: {response.text}")
                    
                    return True
        except Exception as e:
            self.logger.error(f"Error deleting knowledge base: {str(e)}")
            raise Exception(f"Failed to delete knowledge base: {str(e)}")

    async def chat_with_knowledge_base(self, kb_id: str, query: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Chat with a knowledge base using retrieval"""
        if history is None:
            history = []
        
        try:
            # First check if the knowledge base exists
            kb_list = await self.list_knowledge_bases()
            kb_exists = any(kb.get('id') == kb_id for kb in kb_list)
            
            if not kb_exists:
                self.logger.warning(f"Knowledge base with ID {kb_id} not found")
                return {
                    "answer": "Sorry, the specified knowledge base does not exist.",
                    "citations": []
                }
            
            # Use retrieval to get relevant chunks - this is working reliably
            self.logger.info(f"Retrieving chunks for query: '{query}' from knowledge base {kb_id}")
            retrieval_payload = {
                "question": query,
                "dataset_ids": [kb_id],
                "similarity_threshold": 0.2,  # Lower threshold to get more results
                "vector_similarity_weight": 0.3,
                "top_k": 10,
                "highlight": True  # Get highlighted text if possible
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                retrieval_response = await client.post(
                    f"{self.api_url}/api/v1/retrieval",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=retrieval_payload
                )
                
                if retrieval_response.status_code != 200:
                    self.logger.error(f"Failed to retrieve chunks: {retrieval_response.text}")
                    return {
                        "answer": "Sorry, I couldn't retrieve information from the knowledge base.",
                        "citations": []
                    }
                
                retrieval_result = retrieval_response.json()
                self.logger.info(f"Retrieval result: {json.dumps(retrieval_result)[:500]}...")
                
                # Extract chunks from retrieval response
                chunks = []
                if isinstance(retrieval_result, dict):
                    if "data" in retrieval_result and "chunks" in retrieval_result["data"]:
                        chunks = retrieval_result["data"]["chunks"]
                    elif "chunks" in retrieval_result:
                        chunks = retrieval_result["chunks"]
                
                if not chunks:
                    self.logger.warning(f"No chunks found for query: '{query}' in knowledge base {kb_id}")
                    return {
                        "answer": "Sorry, I couldn't find relevant information in the knowledge base for your question.",
                        "citations": []
                    }
                
                self.logger.info(f"Found {len(chunks)} relevant chunks")
                
                # Process the chunks into context and citations
                citations = []
                context_parts = []
                
                for i, chunk in enumerate(chunks[:5]):  # Use top 5 chunks
                    content = chunk.get("content", "")
                    if not content:
                        continue
                        
                    # Add to context parts
                    context_parts.append(content)
                    
                    # Create a citation
                    citations.append({
                        "text": content,
                        "document_id": chunk.get("document_id", "") or chunk.get("id", ""),
                        "document_name": chunk.get("document_keyword", "") or chunk.get("docnm_kwd", ""),
                        "similarity": chunk.get("similarity", 0)
                    })
                
                # Create a simple answer based on the retrieved chunks
                if context_parts:
                    # Format the chunks into a response
                    answer = f"Here's what I found in the knowledge base:\n\n"
                    
                    for i, part in enumerate(context_parts):
                        answer += f"Excerpt {i+1}:\n{part.strip()}\n\n"
                    
                    return {
                        "answer": answer,
                        "citations": citations
                    }
                else:
                    return {
                        "answer": "Sorry, I couldn't find relevant information in the knowledge base for your question.",
                        "citations": []
                    }
        
        except Exception as e:
            self.logger.error(f"Error in chat_with_knowledge_base: {str(e)}")
            return {
                "answer": f"Sorry, I encountered an error: {str(e)}",
                "citations": []
            }

ragflow_service = RAGFlowService() 