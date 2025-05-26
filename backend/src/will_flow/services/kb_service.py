import json
import logging
import uuid
from typing import List, Optional
from datetime import datetime

from opensearchpy import OpenSearch
from opensearchpy.exceptions import NotFoundError

from will_flow.models.knowledge_base import KnowledgeBase, KnowledgeBaseCreate, KnowledgeBaseUpdate, DocumentInfo
from will_flow.core.config import settings


class KBService:
    """Service for managing knowledge bases in OpenSearch"""

    def __init__(self):
        self.client = OpenSearch(
            hosts=[{'host': settings.OPENSEARCH_HOST, 'port': settings.OPENSEARCH_PORT}],
            http_auth=(settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD),
            use_ssl=settings.OPENSEARCH_USE_SSL,
            verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
            ssl_show_warn=False,
        )
        self.index = "knowledge_bases"
        self.logger = logging.getLogger(__name__)
        
        # Ensure index exists
        self._create_index_if_not_exists()

    def _create_index_if_not_exists(self):
        """Create the knowledge_bases index if it doesn't exist"""
        if not self.client.indices.exists(index=self.index):
            self.logger.info(f"Creating index {self.index}")
            
            mappings = {
                "mappings": {
                    "properties": {
                        "name": {"type": "text"},
                        "description": {"type": "text"},
                        "user_email": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "documents": {
                            "type": "nested",
                            "properties": {
                                "doc_id": {"type": "keyword"},
                                "file_name": {"type": "text"},
                                "file_type": {"type": "keyword"},
                                "status": {"type": "keyword"},
                                "upload_time": {"type": "date"},
                                "size_bytes": {"type": "long"}
                            }
                        }
                    }
                }
            }
            
            self.client.indices.create(index=self.index, body=mappings)

    async def create_kb(self, kb: KnowledgeBase) -> KnowledgeBase:
        """Create a new knowledge base"""
        if not kb.id:
            kb.id = str(uuid.uuid4())
        
        kb_dict = kb.model_dump()
        
        self.client.index(
            index=self.index,
            id=kb.id,
            body=kb_dict,
            refresh=True
        )
        
        return kb

    async def get_kb(self, kb_id: str) -> Optional[KnowledgeBase]:
        """Get a knowledge base by ID"""
        try:
            response = self.client.get(index=self.index, id=kb_id)
            kb_data = response["_source"]
            return KnowledgeBase(**kb_data)
        except NotFoundError:
            return None

    async def list_kbs_by_user(self, user_email: str) -> List[KnowledgeBase]:
        """List knowledge bases for a user"""
        query = {
            "query": {
                "term": {
                    "user_email": user_email
                }
            },
            "sort": [
                {"created_at": {"order": "desc"}}
            ]
        }
        
        response = self.client.search(
            index=self.index,
            body=query,
            size=100  # Limit to 100 knowledge bases
        )
        
        kbs = []
        for hit in response["hits"]["hits"]:
            kb_data = hit["_source"]
            kb_data["id"] = hit["_id"]
            kbs.append(KnowledgeBase(**kb_data))
        
        return kbs

    async def update_kb(self, kb_id: str, kb_update: KnowledgeBaseUpdate) -> Optional[KnowledgeBase]:
        """Update a knowledge base"""
        try:
            # Get current KB
            current_kb = await self.get_kb(kb_id)
            if not current_kb:
                return None
            
            # Update fields
            update_data = kb_update.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            # Prepare update body
            update_body = {
                "doc": update_data
            }
            
            # Update in OpenSearch
            self.client.update(
                index=self.index,
                id=kb_id,
                body=update_body,
                refresh=True
            )
            
            # Get updated KB
            return await self.get_kb(kb_id)
        except Exception as e:
            self.logger.error(f"Error updating knowledge base: {e}")
            return None

    async def delete_kb(self, kb_id: str) -> bool:
        """Delete a knowledge base"""
        try:
            self.client.delete(
                index=self.index,
                id=kb_id,
                refresh=True
            )
            return True
        except NotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Error deleting knowledge base: {e}")
            return False

    async def add_document(self, kb_id: str, doc_info: DocumentInfo) -> Optional[KnowledgeBase]:
        """Add a document to a knowledge base"""
        try:
            # Get current KB
            current_kb = await self.get_kb(kb_id)
            if not current_kb:
                return None
            
            # Add document to documents list
            current_kb.documents.append(doc_info)
            current_kb.updated_at = datetime.utcnow()
            
            # Update in OpenSearch
            update_body = {
                "doc": {
                    "documents": [doc.model_dump() for doc in current_kb.documents],
                    "updated_at": current_kb.updated_at
                }
            }
            
            self.client.update(
                index=self.index,
                id=kb_id,
                body=update_body,
                refresh=True
            )
            
            return current_kb
        except Exception as e:
            self.logger.error(f"Error adding document to knowledge base: {e}")
            return None

    async def update_document_status(self, kb_id: str, doc_id: str, status: str) -> Optional[KnowledgeBase]:
        """Update a document's status in a knowledge base"""
        try:
            # Get current KB
            current_kb = await self.get_kb(kb_id)
            if not current_kb:
                return None
            
            # Find and update document
            for doc in current_kb.documents:
                if doc.doc_id == doc_id:
                    doc.status = status
                    break
            
            current_kb.updated_at = datetime.utcnow()
            
            # Update in OpenSearch
            update_body = {
                "doc": {
                    "documents": [doc.model_dump() for doc in current_kb.documents],
                    "updated_at": current_kb.updated_at
                }
            }
            
            self.client.update(
                index=self.index,
                id=kb_id,
                body=update_body,
                refresh=True
            )
            
            return current_kb
        except Exception as e:
            self.logger.error(f"Error updating document status: {e}")
            return None

kb_service = KBService() 