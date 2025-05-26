#!/usr/bin/env python

import os
import json
import httpx
import asyncio
from datetime import datetime

async def test_ragflow_api():
    """Test RAGFlow API with the correct endpoints from documentation"""
    print("Testing RAGFlow API with correct endpoints...")
    
    # Configure RAGFlow API
    api_url = "http://10.147.19.152:8080"
    api_key = "ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. List existing datasets (knowledge bases) using the correct endpoint
            print("\n1. Listing existing datasets (knowledge bases)...")
            response = await client.get(
                f"{api_url}/api/v1/datasets",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code != 200:
                print(f"Failed to list datasets: {response.text}")
                return False
                
            # Parse the response which could be in different formats
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)[:500]}...")
            
            datasets = []
            if isinstance(response_data, dict) and "data" in response_data:
                # Standard response format: {"code": 0, "data": [...]}
                datasets = response_data.get("data", [])
            elif isinstance(response_data, list):
                # Direct list response
                datasets = response_data
            
            print(f"Found {len(datasets)} datasets")
            
            # 2. Create a dataset (knowledge base) using the correct endpoint
            print("\n2. Creating a dataset (knowledge base)...")
            
            # Only include required fields: name
            # Optional fields: description, avatar, embedding_model, etc.
            payload = {
                "name": f"Test KB {datetime.now().strftime('%H:%M:%S')}"
            }
            
            print(f"Request payload: {json.dumps(payload, indent=2)}")
            response = await client.post(
                f"{api_url}/api/v1/datasets",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload
            )
            
            if response.status_code != 200:
                print(f"Failed to create dataset: {response.text}")
                return False
                
            result = response.json()
            print(f"Create dataset response: {json.dumps(result, indent=2)}")
            
            # Extract dataset ID from response
            dataset_id = None
            if isinstance(result, dict):
                if "data" in result and "id" in result["data"]:
                    dataset_id = result["data"]["id"]
                elif "id" in result:
                    dataset_id = result["id"]
            
            if not dataset_id:
                print("Could not find dataset ID in response")
                return False
                
            print(f"Successfully created dataset with ID: {dataset_id}")
            
            # 3. Upload a document using the correct endpoint
            print("\n3. Uploading a document...")
            
            # Create a test document
            test_file_path = "test_api_upload.txt"
            with open(test_file_path, "w") as f:
                f.write("This is a test document for direct API upload test.")
                
            # Upload the document using multipart/form-data
            with open(test_file_path, "rb") as f:
                files = {"file": (test_file_path, f, "text/plain")}
                
                response = await client.post(
                    f"{api_url}/api/v1/datasets/{dataset_id}/documents",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files=files
                )
                
            if response.status_code != 200:
                print(f"Failed to upload document: {response.text}")
                return False
                
            upload_result = response.json()
            print(f"Upload response: {json.dumps(upload_result, indent=2)}")
            
            # Extract document ID
            document_id = None
            if isinstance(upload_result, dict):
                if "data" in upload_result and len(upload_result["data"]) > 0:
                    document_id = upload_result["data"][0].get("id")
            
            if document_id:
                print(f"Successfully uploaded document with ID: {document_id}")
                
                # 4. Parse document to create chunks
                print("\n4. Parsing document...")
                
                parse_payload = {
                    "document_ids": [document_id]
                }
                
                response = await client.post(
                    f"{api_url}/api/v1/datasets/{dataset_id}/chunks",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json=parse_payload
                )
                
                if response.status_code != 200:
                    print(f"Failed to parse document: {response.text}")
                else:
                    print("Document parsing started successfully")
                    
                    # 5. Wait a moment and then list document status
                    await asyncio.sleep(3)
                    print("\n5. Checking document status...")
                    
                    response = await client.get(
                        f"{api_url}/api/v1/datasets/{dataset_id}/documents",
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    
                    if response.status_code != 200:
                        print(f"Failed to list documents: {response.text}")
                    else:
                        docs_result = response.json()
                        print(f"Documents in dataset: {json.dumps(docs_result, indent=2)[:500]}...")
            else:
                print("Document uploaded but could not find document ID in response")
            
            # 6. Test retrieval from the dataset
            print("\n6. Testing retrieval...")
            
            retrieval_payload = {
                "question": "What is this document about?",
                "dataset_ids": [dataset_id],
                "similarity_threshold": 0.2,
                "vector_similarity_weight": 0.3,
                "top_k": 5
            }
            
            response = await client.post(
                f"{api_url}/api/v1/retrieval",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=retrieval_payload
            )
            
            if response.status_code != 200:
                print(f"Failed to retrieve chunks: {response.text}")
            else:
                retrieval_result = response.json()
                print(f"Retrieval response: {json.dumps(retrieval_result, indent=2)[:500]}...")
            
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
                
            print("\nRAGFlow API test completed!")
            return True
    
    except Exception as e:
        print(f"Error during RAGFlow API test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_ragflow_api()) 