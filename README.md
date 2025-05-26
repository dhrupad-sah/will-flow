# Will Flow

A modern AI flow management and chat application that allows users to create, save, and chat with custom AI conversation flows.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [RAGFlow Integration](#ragflow-integration)
- [OpenSearch Queries](#opensearch-queries)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [API Reference](#api-reference)

## Overview

Will Flow is a comprehensive application that enables users to create AI conversation flows with custom system prompts, save them, and have persistent conversations through a thread-based chat interface.

## Features

- **User Management**: Email-based authentication
- **Flow Creation**: Custom system prompts and model selection
- **Thread Management**: Persistent conversations with naming and organization
- **Chat Interface**: Clean and modern UI for conversations
- **Document Understanding**: RAG capabilities through RAGFlow integration
- **OpenSearch Backend**: Efficient storage and retrieval of conversations and flows

## Architecture

### Backend (FastAPI, Python)

- User management with email-based authentication
- Flow creation and management
- Chat functionality using OpenRouter API
- OpenSearch for data storage
- Thread functionality for persistent conversations

### Frontend (Next.js)

- Flow creation and management interface
- Chat interface with thread support
- Email-based user identification
- Modern UI with animations and responsive design

## RAGFlow Integration

This application integrates with [RAGFlow](https://github.com/infiniflow/ragflow) for knowledge base management and document chat capabilities. RAGFlow is an open-source RAG (Retrieval-Augmented Generation) engine based on deep document understanding.

### Configuration

The RAGFlow service is configured in `backend/src/will_flow/services/ragflow_service.py`. It supports two modes:

1. SDK mode (preferred): Uses the `ragflow-sdk` package for API interactions
2. Direct API mode: Falls back to direct HTTP calls if the SDK is not available

### API Endpoints

RAGFlow is hosted at `http://10.147.19.152:8080` with API key `ragflow-ViN2Y0NDI2MzlmODExZjA5YmNlMDI0Mm`.

### Document Upload

Documents are uploaded to RAGFlow using the knowledge base API:

```python
# Using the SDK
from ragflow_sdk import RAGFlow

client = RAGFlow(api_key="YOUR_API_KEY", base_url="YOUR_RAGFLOW_URL")
dataset = client.list_datasets()[0]  # Get first knowledge base

# Upload a document
with open("document.pdf", "rb") as f:
    document_list = [{
        "display_name": "document.pdf",
        "blob": f.read()
    }]
    dataset.upload_documents(document_list)
```

### Troubleshooting

If you encounter issues with file uploads:

1. Ensure the RAGFlow server is accessible
2. Verify the API key is correct
3. Check that the SDK is installed (`pip install ragflow-sdk==0.19.0`)
4. For API errors, check the logs in the backend service

### Fixed Issues

The following issues have been fixed in the RAGFlow integration:

1. **Document upload failures**: Fixed by updating to use the correct SDK method `upload_documents` with the proper payload format `[{"display_name": filename, "blob": content}]` instead of using direct HTTP requests with incorrect endpoints.

2. **Authentication format**: Changed from using `X-API-KEY` header to the correct `Authorization: Bearer {api_key}` format.

3. **Incorrect endpoints**: Updated to use the plural endpoints `/knowledge-bases` instead of singular `/knowledge-base`.

4. **Timeout issues**: Increased timeout for document uploads to 120 seconds to accommodate larger files.

5. **Error handling**: Added better error handling and logging for debugging upload issues.

6. **Status mapping**: Improved document status mapping to correctly interpret various status codes from RAGFlow.

### Testing

Two test scripts are available for verifying the RAGFlow integration:

1. `backend/test_ragflow_sdk.py`: Tests direct SDK functionality
2. `backend/test_ragflow_upload.py`: Tests document upload functionality
3. `backend/test_ragflow_api.py`: Tests the HTTP API endpoints

Run these tests to verify that the integration is working correctly.

## OpenSearch Queries

### Thread Management Queries

#### List All Threads for a User

```json
GET chat_history/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "user_email": "user@example.com" } }
      ]
    }
  },
  "sort": [
    { "updated_at": { "order": "desc" } }
  ]
}
```

#### List Threads for a Specific Flow

```json
GET chat_history/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "user_email": "user@example.com" } },
        { "term": { "flow_id": "flow123" } }
      ]
    }
  },
  "sort": [
    { "updated_at": { "order": "desc" } }
  ]
}
```

#### Get a Specific Thread

```json
GET chat_history/_doc/thread123
```

#### Update Thread Title

```json
POST chat_history/_update/thread123
{
  "doc": {
    "title": "New Thread Title",
    "updated_at": "2023-06-01T12:00:00Z"
  }
}
```

#### Delete a Thread

```json
DELETE chat_history/_doc/thread123
```

#### Add a Message to a Thread

```json
POST chat_history/_update/thread123
{
  "script": {
    "source": "ctx._source.messages.add(params.message); ctx._source.updated_at = params.updated_at",
    "lang": "painless",
    "params": {
      "message": {
        "role": "user",
        "content": "Hello, how are you?",
        "timestamp": "2023-06-01T12:00:00Z"
      },
      "updated_at": "2023-06-01T12:00:00Z"
    }
  }
}
```

### Flow Management Queries

#### List All Flows

```json
GET flows/_search
{
  "query": {
    "match_all": {}
  },
  "sort": [
    { "created_at": { "order": "desc" } }
  ]
}
```

#### List Flows for a User

```json
GET flows/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "creator_email": "user@example.com" } }
      ]
    }
  },
  "sort": [
    { "created_at": { "order": "desc" } }
  ]
}
```

#### Get a Specific Flow

```json
GET flows/_doc/flow123
```

#### Update Flow Details

```json
POST flows/_update/flow123
{
  "doc": {
    "name": "Updated Flow Name",
    "system_prompt": "Updated system prompt",
    "updated_at": "2023-06-01T12:00:00Z"
  }
}
```

#### Delete a Flow

```json
DELETE flows/_doc/flow123
```

### User Management Queries

#### Get User by Email

```json
GET users/_search
{
  "query": {
    "term": {
      "email": "user@example.com"
    }
  }
}
```

#### Create a New User

```json
PUT users/_doc/user123
{
  "email": "user@example.com",
  "created_at": "2023-06-01T12:00:00Z"
}
```

## Setup and Installation

### Prerequisites

- Node.js >= 18.0.0
- Python >= 3.9
- Docker and Docker Compose (for OpenSearch and RAGFlow)

### Backend Setup

1. Clone the repository
   ```
   git clone https://github.com/yourusername/will-flow.git
   cd will-flow/backend
   ```

2. Install dependencies
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables
   ```
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Start OpenSearch
   ```
   docker-compose up -d opensearch
   ```

5. Run the backend server
   ```
   uvicorn will_flow.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory
   ```
   cd ../frontend
   ```

2. Install dependencies
   ```
   npm install
   ```

3. Set up environment variables
   ```
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. Start the development server
   ```
   npm run dev
   ```

### RAGFlow Setup (Optional)

1. Set up system parameters
   ```
   sudo sysctl -w vm.max_map_count=262144
   ```

2. Clone the RAGFlow repository
   ```
   git clone https://github.com/infiniflow/ragflow.git
   cd ragflow/docker
   git checkout -f v0.18.0
   ```

3. Start the RAGFlow server
   ```
   docker compose -f docker-compose.yml up -d
   ```

## Usage

1. Create an account or log in
2. Create a new flow with custom system prompt and model
3. Start a chat with your flow
4. (Optional) Upload documents to create a knowledge base
5. Chat with AI about your documents with accurate citations

## API Reference

### Backend API Endpoints

- **User API**
  - `POST /api/v1/users/`: Create a new user

- **Flow API**
  - `POST /api/v1/flows/`: Create a new flow
  - `GET /api/v1/flows/{flow_id}`: Get flow by ID
  - `GET /api/v1/flows/`: List flows
  - `PUT /api/v1/flows/{flow_id}`: Update flow
  - `DELETE /api/v1/flows/{flow_id}`: Delete flow

- **Chat API**
  - `POST /api/v1/chat/`: Send a chat message
  - `GET /api/v1/chat/session/{session_id}`: Get chat session
  - `GET /api/v1/chat/threads`: List threads
  - `PUT /api/v1/chat/session/{session_id}/title`: Update thread title
  - `DELETE /api/v1/chat/session/{session_id}`: Delete thread

### RAGFlow API (When Integrated)

- **Knowledge Base API**
  - Create and manage knowledge bases
  - Upload and process documents
  - Query document content

- **Chat with Documents API**
  - Ground conversations in document knowledge
  - Retrieve citations and references 