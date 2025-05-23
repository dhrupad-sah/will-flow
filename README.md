# Will Flow

A platform for creating, managing, and chatting with AI flows.

## Features

- Create and save AI conversation flows with different system prompts
- Select from multiple AI models via OpenRouter
- Persistent chat history
- Simple email-based user tracking

## Tech Stack

### Backend
- FastAPI (Python)
- PDM for dependency management
- OpenSearch for data storage
- OpenRouter API for AI model access

### Frontend
- Next.js
- TypeScript
- TailwindCSS

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- Python 3.10+
- Docker (for running OpenSearch)

### Backend Setup

1. Start OpenSearch in Docker:
   ```
   docker run -p 9200:9200 -p 9600:9600 -e "discovery.type=single-node" opensearchproject/opensearch:latest
   ```

2. Navigate to the backend directory:
   ```
   cd backend
   ```

3. Install dependencies:
   ```
   conda activate default
   pdm install
   ```

4. Create a `.env` file based on `.env.example` and add your OpenRouter API key.

5. Start the API server:
   ```
   pdm run python -m src.will_flow.main
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Create a `.env.local` file with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Start the development server:
   ```
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. Enter your email address to sign in
2. Create new flows with custom system prompts
3. Select a flow to chat with
4. Enjoy your conversations! 