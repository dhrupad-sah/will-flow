#!/usr/bin/env python

import os
import json
from ragflow_sdk import RAGFlow

def test_direct_sdk_api():
    """Test RAGFlow SDK direct API calls without default fields"""
    print("Testing RAGFlow SDK direct API calls...")
    
    # Configure RAGFlow SDK client
    api_url = "http://10.147.19.152:8080"
    api_key = "ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm"
    
    try:
        # Create RAGFlow client
        client = RAGFlow(
            api_key=api_key,
            base_url=api_url
        )
        
        # 1. List existing knowledge bases
        print("\n1. Listing existing knowledge bases...")
        datasets = client.list_datasets()
        print(f"Found {len(datasets)} knowledge bases")
        for dataset in datasets:
            print(f"- {dataset.name} (ID: {dataset.id})")
        
        # 2. Create a knowledge base using the low-level API call
        print("\n2. Creating a knowledge base using low-level API call...")
        # Only include name and description to avoid issues with avatar and language
        payload = {
            "name": "Test Direct API KB",
            "description": "Created with direct SDK API call"
        }
        
        # Make the direct API request
        print(f"Request payload: {json.dumps(payload, indent=2)}")
        response = client._request(
            "POST",
            "/api/v1/knowledge-bases",
            json=payload
        )
        
        print(f"Response: {json.dumps(response, indent=2)}")
        
        if "id" in response:
            kb_id = response["id"]
            print(f"Successfully created knowledge base with ID: {kb_id}")
            
            # 3. Upload a document using the direct API
            print("\n3. Uploading a document...")
            
            # Create a test document
            test_file = "test_direct_api_upload.txt"
            with open(test_file, "w") as f:
                f.write("This is a test document for the direct API upload test.")
            
            # Read the file content
            with open(test_file, "rb") as f:
                file_content = f.read()
            
            # Use the SDK but with the correctly formatted document payload
            datasets = client.list_datasets(id=kb_id)
            if datasets:
                dataset = datasets[0]
                
                document_list = [{
                    "display_name": test_file,
                    "blob": file_content
                }]
                
                print(f"Uploading document to KB {kb_id}")
                result = dataset.upload_documents(document_list)
                print(f"Upload result: {result}")
                
                # List documents to verify
                docs = dataset.list_documents()
                print(f"Documents in knowledge base: {len(docs)}")
                for doc in docs:
                    print(f"- {doc.name} (ID: {doc.id}, Status: {getattr(doc, 'run', 'unknown')})")
            
            # Clean up test file
            if os.path.exists(test_file):
                os.remove(test_file)
            
            print("\nDirect SDK API test completed successfully!")
            return True
        else:
            print(f"Failed to create knowledge base. Response: {response}")
            return False
            
    except Exception as e:
        print(f"Error during direct SDK API test: {str(e)}")
        return False

if __name__ == "__main__":
    test_direct_sdk_api() 