#!/usr/bin/env python

import os
import asyncio
import httpx
import json
from pathlib import Path

# Base URL for the API
API_URL = "http://localhost:8000"  # Adjust if your server runs on a different port
TEST_USER_EMAIL = "test@example.com"

async def test_knowledge_base_api():
    """Test the knowledge base API endpoints using direct HTTP requests"""
    print("Testing knowledge base API endpoints...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 1. Create a knowledge base
            print("\n1. Creating a knowledge base...")
            kb_data = {
                "name": f"Test KB {os.urandom(4).hex()}",
                "description": "Created for API testing"
            }
            
            response = await client.post(
                f"{API_URL}/api/v1/knowledge-bases?user_email={TEST_USER_EMAIL}",
                json=kb_data
            )
            
            if response.status_code != 200:
                print(f"Failed to create knowledge base: {response.text}")
                return False
            
            kb = response.json()
            kb_id = kb["id"]
            print(f"Created knowledge base: {kb['name']} (ID: {kb_id})")
            
            # 2. Get the knowledge base
            print("\n2. Getting knowledge base details...")
            response = await client.get(f"{API_URL}/api/v1/knowledge-bases/{kb_id}")
            
            if response.status_code != 200:
                print(f"Failed to get knowledge base: {response.text}")
                return False
            
            kb_details = response.json()
            print(f"Retrieved knowledge base: {kb_details['name']} (Documents: {len(kb_details['documents'])})")
            
            # 3. Upload a document
            print("\n3. Uploading a document...")
            test_file_path = "test_api_upload.txt"
            with open(test_file_path, "w") as f:
                f.write("This is a test document for API testing.")
            
            with open(test_file_path, "rb") as f:
                files = {"file": (os.path.basename(test_file_path), f, "text/plain")}
                response = await client.post(
                    f"{API_URL}/api/v1/knowledge-bases/{kb_id}/documents",
                    files=files
                )
            
            if response.status_code != 200:
                print(f"Failed to upload document: {response.text}")
                return False
            
            doc_info = response.json()
            doc_id = doc_info["doc_id"]
            print(f"Uploaded document: {doc_info['file_name']} (ID: {doc_id}, Status: {doc_info['status']})")
            
            # 4. Check document status
            print("\n4. Checking document status...")
            for _ in range(5):  # Poll a few times
                response = await client.get(
                    f"{API_URL}/api/v1/knowledge-bases/{kb_id}/documents/{doc_id}"
                )
                
                if response.status_code != 200:
                    print(f"Failed to get document status: {response.text}")
                    break
                
                doc_status = response.json()
                print(f"Document status: {doc_status['status']}")
                
                if doc_status['status'] != "processing":
                    break
                
                await asyncio.sleep(2)
            
            # 5. Chat with the knowledge base
            print("\n5. Chatting with the knowledge base...")
            form_data = {
                "query": "What is this document about?",
                "user_email": TEST_USER_EMAIL
            }
            
            try:
                response = await client.post(
                    f"{API_URL}/api/v1/knowledge-bases/{kb_id}/chat",
                    data=form_data
                )
                
                if response.status_code != 200:
                    print(f"Failed to chat with knowledge base: {response.text}")
                else:
                    chat_response = response.json()
                    print(f"Answer: {chat_response.get('answer', 'No answer')}")
                    print(f"Citations: {json.dumps(chat_response.get('citations', []), indent=2)}")
            except Exception as e:
                print(f"Chat error (expected if document is still processing): {str(e)}")
            
            # 6. List all knowledge bases
            print("\n6. Listing all knowledge bases...")
            response = await client.get(
                f"{API_URL}/api/v1/knowledge-bases?user_email={TEST_USER_EMAIL}"
            )
            
            if response.status_code != 200:
                print(f"Failed to list knowledge bases: {response.text}")
                return False
            
            kb_list = response.json()
            print(f"Found {len(kb_list)} knowledge bases:")
            for kb in kb_list:
                print(f"- {kb['name']} (ID: {kb['id']}, Documents: {len(kb['documents'])})")
            
            # 7. Test the debug connection endpoint
            print("\n7. Testing debug connection endpoint...")
            response = await client.get(
                f"{API_URL}/api/v1/knowledge-bases/debug/connection"
            )
            
            if response.status_code != 200:
                print(f"Failed to test connection: {response.text}")
                return False
            
            debug_info = response.json()
            print(f"Connection status: {debug_info.get('status', 'unknown')}")
            print(f"RAGFlow API URL: {debug_info.get('api_url', 'unknown')}")
            
            print("\nKnowledge base API test completed!")
            return True
        
        except Exception as e:
            print(f"Test failed: {str(e)}")
            return False
        
        finally:
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)

if __name__ == "__main__":
    asyncio.run(test_knowledge_base_api()) 