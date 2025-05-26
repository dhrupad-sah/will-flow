#!/usr/bin/env python

import os
import asyncio
from ragflow_sdk import RAGFlow

def test_ragflow_connection():
    """Test RAGFlow SDK connection"""
    print("Testing RAGFlow SDK connection...")
    
    # Configure RAGFlow SDK client
    api_url = "http://10.147.19.152:8080"
    api_key = "ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm"
    
    try:
        ragflow_client = RAGFlow(
            api_key=api_key,
            base_url=api_url
        )
        
        # List knowledge bases (datasets)
        print("Listing knowledge bases...")
        datasets = ragflow_client.list_datasets()
        print(f"Found {len(datasets)} knowledge bases")
        
        for dataset in datasets:
            print(f"- {dataset.name} (ID: {dataset.id})")
            
            # List documents in the knowledge base
            docs = dataset.list_documents()
            print(f"  - Documents: {len(docs)}")
            
            for doc in docs:
                print(f"    - {doc.name} (ID: {doc.id}, Status: {doc.run})")
        
        print("RAGFlow SDK connection test successful!")
        return True
    except Exception as e:
        print(f"RAGFlow SDK connection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_ragflow_connection() 