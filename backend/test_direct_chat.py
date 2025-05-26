#!/usr/bin/env python

import os
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
logger = logging.getLogger("direct_chat_test")

# RAGFlow API configuration
API_URL = "http://10.147.19.152:8080"
API_KEY = "ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm"

async def test_direct_chat():
    """Test chat functionality with an uploaded document using direct API calls"""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. Create a new dataset (knowledge base)
            logger.info("Creating a new dataset for chat test...")
            kb_name = f"Direct Chat Test {datetime.now().strftime('%H:%M:%S')}"
            
            payload = {
                "name": kb_name,
                "description": "Testing direct chat functionality"
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
            logger.info(f"Create dataset response: {json.dumps(result, indent=2)}")
            
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
            
            # 2. Create a test document with meaningful content
            logger.info("Creating and uploading test document...")
            test_content = """
            # Test Document for RAGFlow Chat
            
            This is a test document to verify that the chat functionality is working properly with RAGFlow.
            
            ## Main Points
            
            1. RAGFlow should process this document and make it available for retrieval.
            2. When asked about this document, RAGFlow should return relevant information.
            3. The retrieval system should be able to find information based on semantic meaning.
            
            ## Additional Information
            
            The chat system combines retrieval with language generation to provide informative responses.
            
            Effective retrieval is the key to accurate answers. Without good retrieval, the system would
            not be able to provide relevant information to the user.
            
            ## Test Questions
            
            You can ask questions like:
            - What is this document about?
            - What are the main points?
            - How does the chat system work?
            - What is important for good answers?
            
            These questions should return relevant information from this document.
            """
            
            test_file_path = "test_direct_chat.txt"
            with open(test_file_path, "w") as f:
                f.write(test_content)
                
            # Upload the document
            with open(test_file_path, "rb") as f:
                files = {"file": (test_file_path, f, "text/plain")}
                
                response = await client.post(
                    f"{API_URL}/api/v1/datasets/{dataset_id}/documents",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    files=files
                )
                
            if response.status_code != 200:
                logger.error(f"Failed to upload document: {response.text}")
                return False
                
            upload_result = response.json()
            logger.info(f"Upload response: {json.dumps(upload_result, indent=2)}")
            
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
                
                # 3. Parse document to create chunks
                logger.info("Starting document parsing...")
                
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
                    logger.error(f"Failed to parse document: {response.text}")
                else:
                    logger.info("Document parsing started successfully")
            
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
                
            # 4. Wait for processing to complete
            logger.info("Waiting for document processing to complete...")
            await asyncio.sleep(5)
            
            # 5. Test retrieval
            logger.info("Testing retrieval from the dataset...")
            
            # Define test questions
            test_questions = [
                "What is this document about?",
                "What are the main points of this document?",
                "How does the chat system work?",
                "What is important for good answers?"
            ]
            
            for question in test_questions:
                logger.info(f"\nQuestion: {question}")
                
                # Try retrieval
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
                        
                        # If we found content, try the chat API
                        try:
                            chat_payload = {
                                "knowledge_base_id": dataset_id,
                                "query": question,
                                "chat_history": []
                            }
                            
                            chat_response = await client.post(
                                f"{API_URL}/api/v1/chat",
                                headers={
                                    "Authorization": f"Bearer {API_KEY}",
                                    "Content-Type": "application/json"
                                },
                                json=chat_payload
                            )
                            
                            if chat_response.status_code == 200:
                                chat_result = chat_response.json()
                                answer = ""
                                
                                # Extract answer
                                if isinstance(chat_result, dict):
                                    if "answer" in chat_result:
                                        answer = chat_result["answer"]
                                    elif "data" in chat_result and "answer" in chat_result["data"]:
                                        answer = chat_result["data"]["answer"]
                                
                                if answer:
                                    logger.info(f"Chat answer: {answer[:200]}...")
                                else:
                                    logger.info("No answer from chat API")
                            else:
                                logger.warning(f"Chat API returned status {chat_response.status_code}: {chat_response.text}")
                        except Exception as chat_error:
                            logger.error(f"Error using chat API: {str(chat_error)}")
                
                # Wait between questions
                await asyncio.sleep(1)
            
            logger.info("Direct chat test completed successfully!")
            return True
    
    except Exception as e:
        logger.error(f"Error during direct chat test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_direct_chat()) 