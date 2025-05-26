#!/usr/bin/env python

import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ragflow_chat_test")

# Add the path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(parent_dir))

# Try different import paths
try:
    try:
        # Try direct import
        from will_flow.services.ragflow_service import ragflow_service
        from will_flow.models.knowledge_base import KnowledgeBaseCreate, DocumentInfo
        logger.info("Imported using direct path")
    except ImportError:
        try:
            # Try with src prefix
            from src.will_flow.services.ragflow_service import ragflow_service
            from src.will_flow.models.knowledge_base import KnowledgeBaseCreate, DocumentInfo
            logger.info("Imported using src prefix")
        except ImportError:
            try:
                # Try with backend prefix
                from backend.src.will_flow.services.ragflow_service import ragflow_service
                from backend.src.will_flow.models.knowledge_base import KnowledgeBaseCreate, DocumentInfo
                logger.info("Imported using backend prefix")
            except ImportError:
                # Add more paths and try absolute import
                backend_src_path = os.path.join(parent_dir, "backend", "src")
                sys.path.insert(0, backend_src_path)
                from will_flow.services.ragflow_service import ragflow_service
                from will_flow.models.knowledge_base import KnowledgeBaseCreate, DocumentInfo
                logger.info("Imported using absolute path")
except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    logger.error(f"Paths searched: {sys.path}")
    sys.exit(1)

async def test_chat_with_document():
    """Test chat functionality with an uploaded document"""
    from fastapi import UploadFile
    import io
    
    try:
        # 1. Create a new knowledge base
        logger.info("Creating a new knowledge base for chat test...")
        kb_name = f"Chat Test KB {datetime.now().strftime('%H:%M:%S')}"
        kb_create = KnowledgeBaseCreate(
            name=kb_name,
            description="Testing chat functionality"
        )
        
        kb = await ragflow_service.create_knowledge_base("test@example.com", kb_create)
        logger.info(f"Created knowledge base: {kb.name} (ID: {kb.id})")
        
        # 2. Create a test document with meaningful content
        logger.info("Creating and uploading test document...")
        test_content = """
        # RAGFlow Documentation
        
        RAGFlow is a powerful system for Retrieval Augmented Generation (RAG).
        
        ## Key Features
        
        - Document ingestion and parsing
        - Vector embeddings for semantic search
        - Retrieval of relevant information
        - Integration with LLM systems
        - API for building applications
        
        ## Usage Examples
        
        You can upload documents in various formats including PDF, DOCX, and TXT.
        The system will automatically parse these documents and make them available for retrieval.
        
        When a query is submitted, RAGFlow will find the most relevant chunks of information
        and use them to generate an informative response.
        
        ## Technical Details
        
        RAGFlow uses a combination of vector search and keyword search for optimal retrieval.
        Documents are chunked into smaller pieces for more precise retrieval.
        """
        
        test_filename = f"ragflow_docs_{datetime.now().strftime('%H%M%S')}.txt"
        
        # Create a file-like object
        test_file = io.BytesIO(test_content.encode())
        
        # Create an UploadFile object
        upload_file = UploadFile(
            filename=test_filename,
            file=test_file,
            content_type="text/plain"
        )
        
        # Upload the document
        doc_info = await ragflow_service.upload_document(kb.id, upload_file)
        logger.info(f"Uploaded document: {doc_info.file_name} (ID: {doc_info.doc_id})")
        
        # 3. Wait for document processing to complete
        logger.info("Waiting for document processing...")
        status = "processing"
        max_attempts = 10
        attempts = 0
        
        while status == "processing" and attempts < max_attempts:
            status = await ragflow_service.get_document_status(kb.id, doc_info.doc_id)
            logger.info(f"Document status: {status}")
            
            if status != "processing":
                break
                
            logger.info("Waiting 3 seconds...")
            await asyncio.sleep(3)
            attempts += 1
        
        if status != "ready":
            logger.warning(f"Document processing did not complete successfully. Status: {status}")
            if status == "processing":
                logger.info("Continuing anyway as the document might be partially processed...")
        
        # 4. Ask some test questions
        test_questions = [
            "What is RAGFlow?",
            "What file formats can be uploaded?",
            "How does RAGFlow retrieve information?",
            "What are the main features of RAGFlow?",
            "How are documents processed in RAGFlow?"
        ]
        
        logger.info("Testing chat functionality with various questions...")
        for question in test_questions:
            logger.info(f"\nQuestion: {question}")
            
            # Get response from RAGFlow
            response = await ragflow_service.chat_with_knowledge_base(kb.id, question)
            
            # Log the answer
            logger.info(f"Answer: {response.get('answer', 'No answer provided')}")
            
            # Log citation count
            citations = response.get("citations", [])
            logger.info(f"Citations: {len(citations)}")
            
            # Log first citation if available
            if citations:
                first_citation = citations[0]
                citation_text = first_citation.get("text", "")
                if len(citation_text) > 100:
                    citation_text = citation_text[:100] + "..."
                logger.info(f"First citation: {citation_text}")
            
            # Wait a moment between questions
            await asyncio.sleep(1)
        
        logger.info("Chat test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error during chat test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Set the PYTHONPATH environment variable
    project_root = str(Path(__file__).parent.parent)
    os.environ["PYTHONPATH"] = project_root
    
    # Run the test
    asyncio.run(test_chat_with_document()) 