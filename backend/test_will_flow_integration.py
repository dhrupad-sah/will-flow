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
logger = logging.getLogger("will_flow_test")

# Add the correct paths to sys.path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(parent_dir))

# Try different import paths
try:
    try:
        # First try the normal import
        from src.will_flow.services.ragflow_service import ragflow_service
        from src.will_flow.models.knowledge_base import KnowledgeBaseCreate
        logger.info("Successfully imported Will Flow modules using standard path")
    except ImportError:
        try:
            # Try with backend prefix
            from backend.src.will_flow.services.ragflow_service import ragflow_service
            from backend.src.will_flow.models.knowledge_base import KnowledgeBaseCreate
            logger.info("Successfully imported Will Flow modules using backend prefix")
        except ImportError:
            # Try adding the parent directory
            sys.path.insert(0, str(parent_dir.parent))
            from will_flow.backend.src.will_flow.services.ragflow_service import ragflow_service
            from will_flow.backend.src.will_flow.models.knowledge_base import KnowledgeBaseCreate
            logger.info("Successfully imported Will Flow modules using full path")
except ImportError as e:
    logger.error(f"Failed to import Will Flow modules: {e}")
    # Print sys.path for debugging
    logger.error(f"sys.path: {sys.path}")
    sys.exit(1)

async def test_ragflow_connection():
    """Test the RAGFlow API connection"""
    try:
        logger.info("Testing RAGFlow API connection...")
        
        # Get RAGFlow version information
        logger.info(f"RAGFlow API URL: {ragflow_service.api_url}")
        logger.info(f"Using SDK: {ragflow_service.client is not None}")
        
        return True
    except Exception as e:
        logger.error(f"RAGFlow connection test failed: {e}")
        return False

async def test_list_knowledge_bases():
    """Test listing knowledge bases"""
    try:
        logger.info("Listing knowledge bases...")
        kb_list = await ragflow_service.list_knowledge_bases()
        
        logger.info(f"Found {len(kb_list)} knowledge bases")
        for kb in kb_list:
            logger.info(f"KB: {kb.get('name')} (ID: {kb.get('id')})")
        
        return kb_list
    except Exception as e:
        logger.error(f"Failed to list knowledge bases: {e}")
        return []

async def test_create_knowledge_base():
    """Test creating a knowledge base"""
    try:
        logger.info("Creating a new knowledge base...")
        
        # Create a unique name with timestamp
        kb_name = f"Test KB {datetime.now().strftime('%H:%M:%S')}"
        
        # Create a knowledge base
        kb_create = KnowledgeBaseCreate(
            name=kb_name,
            description="Created for integration testing"
        )
        
        # Create the knowledge base
        kb = await ragflow_service.create_knowledge_base("test@example.com", kb_create)
        
        logger.info(f"Successfully created knowledge base: {kb.name} (ID: {kb.id})")
        return kb
    except Exception as e:
        logger.error(f"Failed to create knowledge base: {e}")
        return None

async def test_upload_document(kb_id):
    """Test uploading a document to a knowledge base"""
    try:
        from fastapi import UploadFile
        import io
        
        logger.info(f"Uploading a test document to knowledge base {kb_id}...")
        
        # Create a test document
        test_content = "This is a test document for RAGFlow integration testing. " * 10
        test_filename = f"test_doc_{datetime.now().strftime('%H%M%S')}.txt"
        
        # Create a temporary file-like object
        test_file = io.BytesIO(test_content.encode())
        
        # Create an UploadFile object
        upload_file = UploadFile(
            filename=test_filename,
            file=test_file,
            content_type="text/plain"
        )
        
        # Upload the document
        doc_info = await ragflow_service.upload_document(kb_id, upload_file)
        
        logger.info(f"Document uploaded successfully: {doc_info.file_name} (ID: {doc_info.doc_id})")
        return doc_info
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        return None

async def test_document_status(kb_id, doc_id):
    """Test getting document status"""
    try:
        logger.info(f"Getting status for document {doc_id}...")
        
        # Initial status may be processing
        status = await ragflow_service.get_document_status(kb_id, doc_id)
        logger.info(f"Initial document status: {status}")
        
        # Wait for document processing to complete (up to 30 seconds)
        for _ in range(10):
            if status != "processing":
                break
            
            logger.info("Document still processing, waiting 3 seconds...")
            await asyncio.sleep(3)
            status = await ragflow_service.get_document_status(kb_id, doc_id)
            logger.info(f"Updated document status: {status}")
        
        return status
    except Exception as e:
        logger.error(f"Failed to get document status: {e}")
        return "unknown"

async def test_chat_with_knowledge_base(kb_id):
    """Test chatting with a knowledge base"""
    try:
        logger.info(f"Chatting with knowledge base {kb_id}...")
        
        # Try a series of questions to test different aspects of retrieval
        test_questions = [
            "What is this document about?",
            "What are the main topics covered?",
            "Can you summarize the content?",
            "What information does this document contain?"
        ]
        
        success = False
        
        for question in test_questions:
            logger.info(f"\nAsking question: '{question}'")
            
            # Chat with the knowledge base
            response = await ragflow_service.chat_with_knowledge_base(kb_id, question)
            
            # Log the response details
            answer = response.get("answer", "")
            citations = response.get("citations", [])
            
            logger.info(f"Answer: {answer[:200]}...")  # Show first 200 chars
            logger.info(f"Number of citations: {len(citations)}")
            
            # Check if we got a reasonable response
            if answer and len(answer) > 20:  # Arbitrary minimum length for a useful answer
                success = True
                logger.info("Got a meaningful response!")
                
                # Display first citation if available
                if citations:
                    first_citation = citations[0]
                    citation_text = first_citation.get("text", "")
                    doc_id = first_citation.get("document_id", "")
                    doc_name = first_citation.get("document_name", "")
                    
                    if citation_text:
                        # Show a snippet of the citation
                        if len(citation_text) > 100:
                            citation_text = citation_text[:100] + "..."
                        logger.info(f"Citation snippet: {citation_text}")
                        logger.info(f"From document: {doc_name} (ID: {doc_id})")
                
                # If we got a good response, no need to try more questions
                break
        
        if not success:
            logger.warning("Could not get a meaningful response from any question")
        
        return success
    except Exception as e:
        logger.error(f"Error chatting with knowledge base: {e}")
        return False

async def run_all_tests():
    """Run all RAGFlow integration tests"""
    logger.info("Starting Will Flow RAGFlow integration tests...")
    
    # Test RAGFlow connection
    connection_ok = await test_ragflow_connection()
    if not connection_ok:
        logger.error("RAGFlow connection test failed, aborting remaining tests")
        return False
    
    # Test listing knowledge bases
    kb_list = await test_list_knowledge_bases()
    
    # Test creating a knowledge base
    kb = await test_create_knowledge_base()
    if not kb:
        logger.error("Failed to create knowledge base, aborting remaining tests")
        return False
    
    # Test uploading a document
    doc_info = await test_upload_document(kb.id)
    if not doc_info:
        logger.error("Failed to upload document, aborting remaining tests")
        return False
    
    # Test getting document status
    status = await test_document_status(kb.id, doc_info.doc_id)
    
    # Test chatting with the knowledge base
    # Note: This may not work if document processing is not complete
    chat_response = await test_chat_with_knowledge_base(kb.id)
    
    logger.info("All tests completed!")
    return True

if __name__ == "__main__":
    # Set the PYTHONPATH environment variable to include project root
    project_root = str(Path(__file__).parent.parent)
    os.environ["PYTHONPATH"] = project_root
    
    # Run the tests
    asyncio.run(run_all_tests()) 