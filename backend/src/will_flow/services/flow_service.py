from datetime import datetime
from typing import List, Optional

from opensearchpy import OpenSearch

from will_flow.db.opensearch import opensearch_client
from will_flow.models.flow import Flow, FlowCreate, FlowUpdate


class FlowService:
    def __init__(self, client: OpenSearch = opensearch_client):
        self.client = client
        self.index = "flows"

    async def create_flow(self, flow_create: FlowCreate) -> Flow:
        flow_dict = flow_create.model_dump()
        flow_dict["created_at"] = datetime.utcnow().isoformat()
        flow_dict["updated_at"] = flow_dict["created_at"]
        
        result = self.client.index(
            index=self.index,
            body=flow_dict,
            refresh=True
        )
        
        flow_dict["id"] = result["_id"]
        return Flow(**flow_dict)
    
    async def get_flow(self, flow_id: str) -> Optional[Flow]:
        try:
            result = self.client.get(
                index=self.index,
                id=flow_id
            )
            flow_data = result["_source"]
            flow_data["id"] = result["_id"]
            return Flow(**flow_data)
        except Exception as e:
            print(f"Error fetching flow: {e}")
            return None
    
    async def update_flow(self, flow_id: str, flow_update: FlowUpdate) -> Optional[Flow]:
        try:
            # Get existing flow
            existing_flow = await self.get_flow(flow_id)
            if not existing_flow:
                return None
            
            # Update fields
            update_data = flow_update.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Perform update
            self.client.update(
                index=self.index,
                id=flow_id,
                body={"doc": update_data},
                refresh=True
            )
            
            # Get updated flow
            return await self.get_flow(flow_id)
        except Exception as e:
            print(f"Error updating flow: {e}")
            return None
    
    async def delete_flow(self, flow_id: str) -> bool:
        try:
            self.client.delete(
                index=self.index,
                id=flow_id,
                refresh=True
            )
            return True
        except Exception as e:
            print(f"Error deleting flow: {e}")
            return False
    
    async def list_flows(self, creator_email: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Flow]:
        try:
            query = {"match_all": {}}
            
            if creator_email:
                query = {
                    "term": {
                        "creator_email": creator_email
                    }
                }
            
            result = self.client.search(
                index=self.index,
                body={
                    "query": query,
                    "from": offset,
                    "size": limit,
                    "sort": [
                        {"created_at": {"order": "desc"}}
                    ]
                }
            )
            
            flows = []
            for hit in result["hits"]["hits"]:
                flow_data = hit["_source"]
                flow_data["id"] = hit["_id"]
                flows.append(Flow(**flow_data))
            
            return flows
        except Exception as e:
            print(f"Error listing flows: {e}")
            return []