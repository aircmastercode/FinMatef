# FinMate AI Platform - Backend

This is the backend service for the FinMate AI Platform, a conversational AI system for LenDen Club that provides financial information and assistance to users.

## Architecture

The backend uses a modular agent-based architecture with the following components:

### Agents

- **Conductor Agent**: Orchestrates the flow of information between specialized agents
- **Multi-Intent Agent**: Handles queries with multiple intents or questions
- **Data Ingestion Agent**: Processes documents and extracts knowledge
- **URL Scraper Agent**: Extracts content from web URLs
- **Query Handler Agent**: Processes user queries and retrieves knowledge
- **Response Combiner Agent**: Synthesizes responses from multiple sources
- **Escalation Agent**: Handles queries that require human intervention
- **Web Search Agent**: Searches the web for current information

### Services

- **LLM Service**: Handles interactions with OpenAI's GPT models
- **Memory Service**: Manages conversation history and user memory
- **Transcription Service**: Converts voice input to text
- **Storage Service**: Handles file storage and retrieval

### Database Interfaces

- **Graph DB**: Interface for Neo4j graph database
- **Vector DB**: Interface for vector database operations
- **User DB**: Interface for user data management
- **Cognee Client**: Interface for Cognee knowledge base

## Setup and Deployment

### Local Development

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with necessary configuration (see `.env.example`)

4. Run the application:
   ```
   uvicorn main:app --reload
   ```

### Docker Deployment

See the [DEPLOY.md](DEPLOY.md) file for detailed deployment instructions.

## API Endpoints

The API provides two main flows:

### Admin Flow

- `/admin/upload`: Upload documents to the knowledge base
- `/admin/manage-knowledge`: Manage knowledge base entries
- `/admin/escalations`: Handle escalated queries

### User Flow

- `/user/query`: Submit text queries
- `/user/voice`: Submit voice queries
- `/user/history`: Retrieve conversation history

## Development

### Adding a New Agent

1. Create a new file in the `agents` directory
2. Implement the agent class extending the base `Agent` class
3. Register the agent in `agents/__init__.py`
4. Add agent initialization in the dependency injection system

### Testing

Run tests with:
```
pytest
```

## License

Proprietary - All rights reserved 