#!/usr/bin/env python

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path so we can import will_flow modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.will_flow.services.ragflow_service import ragflow_service
    from src.will_flow.models.knowledge_base import KnowledgeBaseCreate
except ImportError:
    print("Adjusting import paths...")
    from backend.src.will_flow.services.ragflow_service import ragflow_service
    from backend.src.will_flow.models.knowledge_base import KnowledgeBaseCreate

async def test_will_flow_ragflow():
    """Test the RAGFlow integration through our Will Flow backend service"""
    print("Testing Will Flow RAGFlow integration...")
    
    try:
        # 1. List knowledge bases through our service
        print("\n1. Listing knowledge bases...")
        kb_list = await ragflow_service.list_knowledge_bases()
        print(f"Found {len(kb_list)} knowledge bases")
        for kb in kb_list:
            print(f"- {kb.get('name', 'No Name')} (ID: {kb.get('id', 'No ID')})")
        
        # 2. Create a test knowledge base
        print("\n2. Creating a test knowledge base...")
        test_kb = KnowledgeBaseCreate(
            name=f"Test KB {os.urandom(4).hex()}",
            description="Created for testing Will Flow RAGFlow integration"
        )
        kb = await ragflow_service.create_knowledge_base("test@example.com", test_kb)
        print(f"Created knowledge base: {kb.name} (ID: {kb.id})")
        
        # 3. Create a sample test file
        print("\n3. Creating a sample test file...")
        test_file_path = "test_upload_will_flow.txt"
        with open(test_file_path, "w") as f:
            f.write("This is a test document for Will Flow RAGFlow integration.")
        
        # Create a mock UploadFile object
        class MockUploadFile:
            def __init__(self, filename, content_type):
                self.filename = filename
                self.content_type = content_type
                self._content = None
            
            async def read(self):
                if not self._content:
                    with open(test_file_path, "rb") as f:
                        self._content = f.read()
                return self._content
        
        mock_file = MockUploadFile(filename=test_file_path, content_type="text/plain")
        
        # 4. Upload a document
        print("\n4. Uploading a document...")
        doc_info = await ragflow_service.upload_document(kb.id, mock_file)
        print(f"Uploaded document: {doc_info.file_name} (ID: {doc_info.doc_id}, Status: {doc_info.status})")
        
        # 5. Check document status
        print("\n5. Checking document status...")
        for _ in range(5):  # Poll a few times
            status = await ragflow_service.get_document_status(kb.id, doc_info.doc_id)
            print(f"Document status: {status}")
            if status != "processing":
                break
            await asyncio.sleep(2)
        
        # 6. Chat with the knowledge base
        print("\n6. Chatting with the knowledge base...")
        try:
            response = await ragflow_service.chat_with_knowledge_base(
                kb.id, 
                "What is this document about?", 
                []
            )
            print(f"Answer: {response.get('answer', 'No answer')}")
            print(f"Citations: {response.get('citations', [])}")
        except Exception as e:
            print(f"Chat error (expected if document is still processing): {str(e)}")
        
        print("\nRAGFlow integration test completed!")
        return True
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    asyncio.run(test_will_flow_ragflow()) 