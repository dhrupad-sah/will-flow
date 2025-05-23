# Will Flow Backend

FastAPI backend for the Will Flow platform.

## Setup

1. Install dependencies:
   ```
   conda activate default
   pdm install
   ```

2. Create a `.env` file with:
   ```
   # OpenSearch Configuration
   OPENSEARCH_HOST=localhost
   OPENSEARCH_PORT=9200
   OPENSEARCH_USER=
   OPENSEARCH_PASSWORD=
   OPENSEARCH_USE_SSL=false
   OPENSEARCH_VERIFY_CERTS=false

   # OpenRouter Configuration
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

   # CORS Configuration
   CORS_ORIGINS=http://localhost:3000
   ```

3. Start the server:
   ```
   pdm run python -m src.will_flow.main
   ```

4. Visit [http://localhost:8000/docs](http://localhost:8000/docs) for API documentation.

## API Endpoints

- `/api/v1/users/`: User management
- `/api/v1/flows/`: Flow CRUD operations
- `/api/v1/chat/`: Chat with flows

## Development

Run tests:
```
pdm run pytest
```

Format code:
```
pdm run black .
pdm run isort .
```

Lint code:
```
pdm run flake8
```
