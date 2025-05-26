#!/usr/bin/env python

import os
import time
from ragflow_sdk import RAGFlow

def test_document_upload(file_path=None):
    """Test document upload to RAGFlow"""
    print("Testing RAGFlow document upload...")
    
    # Configure RAGFlow SDK client
    api_url = "http://10.147.19.152:8080"
    api_key = "ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm"
    
    # Use a default test file if none provided
    if not file_path:
        file_path = "test_upload.txt"
        # Create a simple test file
        with open(file_path, "w") as f:
            f.write("This is a test document for RAGFlow upload.")
    
    try:
        ragflow_client = RAGFlow(
            api_key=api_key,
            base_url=api_url
        )
        
        # List knowledge bases (datasets)
        print("Listing knowledge bases...")
        datasets = ragflow_client.list_datasets()
        
        if not datasets:
            print("No knowledge bases found. Creating a new one...")
            dataset = ragflow_client.create_dataset(
                name="Test Upload KB",
                description="Created for testing document uploads"
            )
            print(f"Created knowledge base: {dataset.name} (ID: {dataset.id})")
        else:
            dataset = datasets[0]
            print(f"Using existing knowledge base: {dataset.name} (ID: {dataset.id})")
        
        # Read the file
        print(f"Reading file: {file_path}")
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        # Upload the document
        file_name = os.path.basename(file_path)
        print(f"Uploading document {file_name} to knowledge base...")
        
        document_list = [{
            "display_name": file_name,
            "blob": file_content
        }]
        
        dataset.upload_documents(document_list)
        print("Document upload request sent")
        
        # List documents to verify
        time.sleep(2)  # Give a little time for processing
        docs = dataset.list_documents()
        print(f"Knowledge base has {len(docs)} documents")
        
        for doc in docs:
            print(f"- {doc.name} (ID: {doc.id}, Status: {doc.run})")
        
        print("RAGFlow document upload test completed!")
        return True
    except Exception as e:
        print(f"RAGFlow document upload test failed: {str(e)}")
        return False
    finally:
        # Clean up test file if we created one
        if not file_path and os.path.exists("test_upload.txt"):
            os.remove("test_upload.txt")

if __name__ == "__main__":
    # You can specify a file path as an argument
    import sys
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    test_document_upload(file_path) 