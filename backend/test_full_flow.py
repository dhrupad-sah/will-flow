#!/usr/bin/env python

import os
import sys
import json
import httpx
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("full_flow_test")

# RAGFlow API configuration
API_URL = "http://10.147.19.152:8080"
API_KEY = "ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm"

async def test_full_flow():
    """Test the full flow of creating a KB, uploading a document, and chatting with it"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Step 1: Create a dataset (knowledge base)
            logger.info("Step 1: Creating a dataset (knowledge base)...")
            kb_name = f"Full Flow Test {datetime.now().strftime('%H:%M:%S')}"
            
            payload = {
                "name": kb_name,
                "description": "Testing the full document upload and chat flow"
            }
            
            response = await client.post(
                f"{API_URL}/api/v1/datasets",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to create dataset: {response.text}")
                return False
                
            result = response.json()
            
            # Extract dataset ID from response
            dataset_id = None
            if isinstance(result, dict):
                if "data" in result and "id" in result["data"]:
                    dataset_id = result["data"]["id"]
                elif "id" in result:
                    dataset_id = result["id"]
            
            if not dataset_id:
                logger.error("Could not find dataset ID in response")
                return False
                
            logger.info(f"Created dataset with ID: {dataset_id}")
            
            # Step 2: Upload a document
            logger.info("\nStep 2: Uploading a document...")
            
            # Create a sample document
            sample_doc = """
# RAGFlow Integration Documentation

## Overview

This document explains how to integrate RAGFlow with Will Flow for document-based chat capabilities.

## Integration Steps

1. Create a knowledge base in RAGFlow
2. Upload documents to the knowledge base
3. Process the documents for retrieval
4. Implement chat functionality using the retrieval API

## API Endpoints

The RAGFlow API provides several endpoints:

- `/api/v1/datasets` - For managing knowledge bases
- `/api/v1/datasets/{id}/documents` - For uploading documents
- `/api/v1/datasets/{id}/chunks` - For processing documents
- `/api/v1/retrieval` - For retrieving relevant chunks

## Implementation Details

When implementing document chat, the process should:

1. Allow users to create knowledge bases
2. Enable document uploads in various formats
3. Process uploaded documents into chunks
4. Retrieve relevant chunks based on user queries
5. Present the information in a user-friendly way

## Common Issues

- Ensure you're using the correct API endpoints
- Check document processing status before attempting retrieval
- Handle different response formats from the API
- Implement proper error handling and fallbacks

## Conclusion

By following these guidelines, you can successfully integrate RAGFlow with Will Flow to enable document-based chat capabilities.
"""
            
            # Create a temporary file
            doc_filename = "ragflow_integration_doc.txt"
            with open(doc_filename, "w") as f:
                f.write(sample_doc)
            
            # Upload the document
            with open(doc_filename, "rb") as f:
                files = {"file": (doc_filename, f, "text/plain")}
                
                response = await client.post(
                    f"{API_URL}/api/v1/datasets/{dataset_id}/documents",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    files=files
                )
            
            if response.status_code != 200:
                logger.error(f"Failed to upload document: {response.text}")
                return False
            
            upload_result = response.json()
            
            # Extract document ID
            document_id = None
            if isinstance(upload_result, dict):
                if "data" in upload_result and len(upload_result["data"]) > 0:
                    document_id = upload_result["data"][0].get("id")
                elif "id" in upload_result:
                    document_id = upload_result["id"]
            
            if not document_id:
                logger.warning("Could not extract document ID, but continuing test")
            else:
                logger.info(f"Uploaded document with ID: {document_id}")
            
            # Clean up temporary file
            if os.path.exists(doc_filename):
                os.remove(doc_filename)
            
            # Step 3: Process the document
            if document_id:
                logger.info("\nStep 3: Processing the document...")
                
                parse_payload = {
                    "document_ids": [document_id]
                }
                
                response = await client.post(
                    f"{API_URL}/api/v1/datasets/{dataset_id}/chunks",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=parse_payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed to start document processing: {response.text}")
                else:
                    logger.info("Document processing started successfully")
            
            # Step 4: Wait for processing to complete
            logger.info("\nStep 4: Waiting for document processing to complete...")
            await asyncio.sleep(5)  # Give some time for processing to start
            
            # Check document status (optional - we're using a small document that should process quickly)
            if document_id:
                try:
                    response = await client.get(
                        f"{API_URL}/api/v1/datasets/{dataset_id}/documents/{document_id}",
                        headers={"Authorization": f"Bearer {API_KEY}"}
                    )
                    
                    if response.status_code == 200:
                        status_result = response.json()
                        status = "unknown"
                        
                        if isinstance(status_result, dict):
                            if "data" in status_result and "run" in status_result["data"]:
                                status = status_result["data"]["run"]
                            elif "run" in status_result:
                                status = status_result["run"]
                        
                        logger.info(f"Document processing status: {status}")
                    else:
                        logger.warning(f"Failed to get document status: {response.text}")
                except Exception as e:
                    logger.warning(f"Error checking document status: {str(e)}")
            
            # Step 5: Test retrieval with different questions
            logger.info("\nStep 5: Testing retrieval with different questions...")
            
            test_questions = [
                "What is this document about?",
                "What are the API endpoints for RAGFlow?",
                "What are the integration steps?",
                "What are common issues to watch out for?",
                "How do I implement document chat?"
            ]
            
            for question in test_questions:
                logger.info(f"\nQuestion: {question}")
                
                retrieval_payload = {
                    "question": question,
                    "dataset_ids": [dataset_id],
                    "similarity_threshold": 0.2,
                    "vector_similarity_weight": 0.3,
                    "top_k": 5
                }
                
                response = await client.post(
                    f"{API_URL}/api/v1/retrieval",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json=retrieval_payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Failed retrieval for question '{question}': {response.text}")
                    continue
                
                retrieval_result = response.json()
                
                # Extract chunks
                chunks = []
                if isinstance(retrieval_result, dict):
                    if "data" in retrieval_result and "chunks" in retrieval_result["data"]:
                        chunks = retrieval_result["data"]["chunks"]
                    elif "chunks" in retrieval_result:
                        chunks = retrieval_result["chunks"]
                
                logger.info(f"Retrieved {len(chunks)} chunks")
                
                if chunks:
                    # Show the first chunk
                    first_chunk = chunks[0]
                    content = first_chunk.get("content", "")
                    
                    if content:
                        # Truncate for display
                        if len(content) > 200:
                            content = content[:200] + "..."
                        logger.info(f"First chunk: {content}")
                        
                        # Create a simple answer based on the retrieved chunks
                        answer = f"Here's what I found for '{question}':\n\n"
                        
                        for i, chunk in enumerate(chunks[:3]):
                            chunk_content = chunk.get("content", "").strip()
                            if chunk_content:
                                answer += f"Excerpt {i+1}:\n{chunk_content}\n\n"
                        
                        logger.info(f"Answer: {answer[:200]}...")
                else:
                    logger.info("No relevant chunks found for this question")
                
                # Wait between questions
                await asyncio.sleep(1)
            
            logger.info("\nFull flow test completed successfully!")
            return True
    
    except Exception as e:
        logger.error(f"Error during full flow test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_full_flow()) 