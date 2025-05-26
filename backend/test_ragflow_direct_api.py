#!/usr/bin/env python

import os
import json
import httpx
import asyncio
from datetime import datetime

async def test_direct_api():
    """Test RAGFlow direct API calls without SDK to avoid default fields"""
    print("Testing RAGFlow direct API calls...")
    
    # Configure RAGFlow API
    api_url = "http://10.147.19.152:8080"
    api_key = "ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. List existing knowledge bases
            print("\n1. Listing existing knowledge bases...")
            response = await client.get(
                f"{api_url}/api/v1/knowledge-bases",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code != 200:
                print(f"Failed to list knowledge bases: {response.text}")
                return False
                
            # Handle the response which could be a list or an object with items
            response_data = response.json()
            kb_list = []
            
            if isinstance(response_data, dict) and "items" in response_data:
                kb_list = response_data.get("items", [])
            elif isinstance(response_data, list):
                kb_list = response_data
            
            print(f"Found {len(kb_list)} knowledge bases")
            
            # Debug print the response for reference
            print(f"Response type: {type(response_data)}")
            print(f"Response content: {json.dumps(response_data, indent=2)[:500]}...")
            
            # Print KB list with safe attribute access
            for i, kb in enumerate(kb_list):
                if isinstance(kb, dict):
                    name = kb.get('name', 'Unknown')
                    kb_id = kb.get('id', 'Unknown')
                    print(f"- {name} (ID: {kb_id})")
                else:
                    print(f"- KB {i}: {kb}")
            
            # 2. Create a knowledge base using direct API
            print("\n2. Creating a knowledge base using direct API...")
            
            # Only include name and description to avoid issues with avatar and language
            payload = {
                "name": f"Test Direct API KB {datetime.now().strftime('%H:%M:%S')}",
                "description": "Created with direct API call"
            }
            
            print(f"Request payload: {json.dumps(payload, indent=2)}")
            response = await client.post(
                f"{api_url}/api/v1/knowledge-bases",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload
            )
            
            if response.status_code != 200:
                print(f"Failed to create knowledge base: {response.text}")
                return False
                
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            kb_id = None
            if isinstance(result, dict):
                kb_id = result.get("id")
            
            if not kb_id:
                print("No ID in response")
                return False
                
            print(f"Successfully created knowledge base with ID: {kb_id}")
            
            # 3. Upload a document
            print("\n3. Uploading a document...")
            
            # Create a test document
            test_file = "test_direct_api_upload.txt"
            with open(test_file, "w") as f:
                f.write("This is a test document for direct API upload test.")
                
            # Upload the document
            with open(test_file, "rb") as f:
                files = {"file": (test_file, f, "text/plain")}
                
                response = await client.post(
                    f"{api_url}/api/v1/knowledge-bases/{kb_id}/documents",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files=files
                )
                
            if response.status_code != 200:
                print(f"Failed to upload document: {response.text}")
                return False
                
            result = response.json()
            print(f"Upload response: {json.dumps(result, indent=2)}")
            
            doc_id = None
            if isinstance(result, dict):
                doc_id = result.get("id") or result.get("doc_id")
                
            if doc_id:
                print(f"Successfully uploaded document with ID: {doc_id}")
            else:
                print("Document uploaded but no ID returned")
            
            # Clean up test file
            if os.path.exists(test_file):
                os.remove(test_file)
                
            print("\nDirect API test completed successfully!")
            return True
    
    except Exception as e:
        print(f"Error during direct API test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_direct_api()) 