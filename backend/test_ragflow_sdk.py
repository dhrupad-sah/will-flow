#!/usr/bin/env python
import os
from ragflow_sdk import RAGFlow

# Configure RAGFlow SDK client
ragflow_client = RAGFlow(
    api_key="ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm",
    base_url="http://10.147.19.152:8080"
)

def list_knowledge_bases():
    """List all knowledge bases in RAGFlow"""
    try:
        print("Listing knowledge bases...")
        datasets = ragflow_client.list_datasets()
        print(f"Found {len(datasets)} knowledge bases")
        for dataset in datasets:
            print(f"- {dataset.name} (ID: {dataset.id})")
        return datasets
    except Exception as e:
        print(f"Error listing knowledge bases: {str(e)}")
        return []

def create_knowledge_base(name, description=""):
    """Create a new knowledge base in RAGFlow"""
    try:
        print(f"Creating knowledge base '{name}'...")
        dataset = ragflow_client.create_dataset(
            name=name,
            description=description
        )
        print(f"Created knowledge base: {dataset.name} (ID: {dataset.id})")
        return dataset
    except Exception as e:
        print(f"Error creating knowledge base: {str(e)}")
        return None

def upload_document(dataset, file_path):
    """Upload a document to a knowledge base using the correct SDK method"""
    try:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        
        # Read file content
        with open(file_path, "rb") as f:
            file_content = f.read()
        
        file_name = os.path.basename(file_path)
        print(f"Uploading file '{file_name}' to knowledge base...")
        
        # According to RAGFlow SDK docs, we need to use upload_documents method
        # with a list of dictionaries containing display_name and blob
        document_list = [{
            "display_name": file_name,
            "blob": file_content
        }]
        
        # Upload document
        dataset.upload_documents(document_list)
        print(f"File uploaded successfully")
        
        # List documents to verify
        docs = dataset.list_documents()
        print(f"Knowledge base has {len(docs)} documents")
        for doc in docs:
            print(f"- {doc.name} (ID: {doc.id}, Status: {doc.run})")
        
        return docs
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        return None

if __name__ == "__main__":
    # List existing knowledge bases
    datasets = list_knowledge_bases()
    
    # Create a test knowledge base if needed
    if not datasets:
        dataset = create_knowledge_base("Test KB", "Created for testing")
    else:
        dataset = datasets[0]  # Use the first knowledge base
    
    if dataset:
        # Test uploading a document (replace with actual file path)
        test_file = "/path/to/test/document.pdf"  # Replace with actual file path
        upload_document(dataset, test_file) 