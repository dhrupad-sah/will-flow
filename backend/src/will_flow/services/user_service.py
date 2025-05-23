from datetime import datetime
from typing import Optional

from opensearchpy import OpenSearch

from will_flow.db.opensearch import opensearch_client
from will_flow.models.user import User, UserCreate, UserInDB


class UserService:
    def __init__(self, client: OpenSearch = opensearch_client):
        self.client = client
        self.index = "users"

    async def create_user(self, user_create: UserCreate) -> User:
        user_in_db = UserInDB(**user_create.model_dump())
        user_dict = user_in_db.model_dump()
        
        # Convert datetime objects to strings for OpenSearch
        for field in ["created_at", "last_login"]:
            if user_dict.get(field):
                user_dict[field] = user_dict[field].isoformat()
        
        # Check if user already exists
        existing = self.client.search(
            index=self.index,
            body={
                "query": {
                    "term": {
                        "email": user_create.email
                    }
                }
            }
        )
        
        if existing["hits"]["total"]["value"] > 0:
            user_id = existing["hits"]["hits"][0]["_id"]
            # Update last login time
            self.client.update(
                index=self.index,
                id=user_id,
                body={
                    "doc": {
                        "last_login": datetime.utcnow().isoformat()
                    }
                }
            )
            
            user_data = existing["hits"]["hits"][0]["_source"]
            return User(**user_data)
        
        # Create new user
        result = self.client.index(
            index=self.index,
            body=user_dict,
            refresh=True
        )
        
        user_dict["id"] = result["_id"]
        return User(**user_dict)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        try:
            result = self.client.search(
                index=self.index,
                body={
                    "query": {
                        "term": {
                            "email": email
                        }
                    }
                }
            )
            
            if result["hits"]["total"]["value"] > 0:
                user_data = result["hits"]["hits"][0]["_source"]
                user_data["id"] = result["hits"]["hits"][0]["_id"]
                return User(**user_data)
            
            return None
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None 