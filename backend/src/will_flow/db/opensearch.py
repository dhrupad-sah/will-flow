from opensearchpy import OpenSearch, RequestsHttpConnection

from will_flow.core.config import settings


def get_opensearch_client():
    """Create and return an OpenSearch client."""
    host = settings.OPENSEARCH_HOST
    port = settings.OPENSEARCH_PORT
    auth = None
    
    if settings.OPENSEARCH_USER and settings.OPENSEARCH_PASSWORD:
        auth = (settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD)
    
    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=auth,
        use_ssl=settings.OPENSEARCH_USE_SSL,
        verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
        connection_class=RequestsHttpConnection,
    )
    
    return client


def initialize_indices(client: OpenSearch):
    """Initialize OpenSearch indices if they don't exist."""
    # Users index
    if not client.indices.exists(index="users"):
        user_mappings = {
            "mappings": {
                "properties": {
                    "email": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "last_login": {"type": "date"},
                }
            }
        }
        client.indices.create(index="users", body=user_mappings)
    
    # Flows index
    if not client.indices.exists(index="flows"):
        flow_mappings = {
            "mappings": {
                "properties": {
                    "name": {"type": "text"},
                    "description": {"type": "text"},
                    "system_prompt": {"type": "text"},
                    "creator_email": {"type": "keyword"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "model": {"type": "keyword"},
                }
            }
        }
        client.indices.create(index="flows", body=flow_mappings)
    
    # Chat history index
    if not client.indices.exists(index="chat_history"):
        chat_history_mappings = {
            "mappings": {
                "properties": {
                    "flow_id": {"type": "keyword"},
                    "user_email": {"type": "keyword"},
                    "messages": {
                        "type": "nested",
                        "properties": {
                            "role": {"type": "keyword"},
                            "content": {"type": "text"},
                            "timestamp": {"type": "date"},
                        }
                    },
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            }
        }
        client.indices.create(index="chat_history", body=chat_history_mappings)


# Get the client and initialize
opensearch_client = get_opensearch_client()
try:
    initialize_indices(opensearch_client)
except Exception as e:
    print(f"Error initializing OpenSearch indices: {e}")
    # For development, we'll continue even if OpenSearch is not available
    # In production, you might want to fail fast here 