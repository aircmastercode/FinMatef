# FinMate AI Platform

A conversational AI platform for LenDen Club that provides financial information and assistance to users through a modular agent-based architecture.

## Overview

FinMate is an advanced AI assistant designed specifically for LenDen Club to handle customer inquiries, provide financial information, and assist with various tasks. The system uses a sophisticated agent-based architecture that allows it to process complex queries, maintain context, and provide accurate responses.

## Key Features

- **Modular Agent Architecture**: Specialized agents work together to handle different aspects of user interactions
- **Dual Processing Flows**: Separate flows for admin (data upload) and user (query) interactions
- **Persistent Memory**: User-specific conversation history and context
- **Knowledge Integration**: Neo4j graph database and vector database for efficient knowledge retrieval
- **Voice Interface**: Support for voice queries with transcription
- **Escalation System**: Automatic escalation to human operators when needed

## Project Structure

- **backend_new/**: New modular agent-based backend (recommended)
  - **agents/**: Specialized agent implementations
  - **services/**: Core services like LLM, memory, transcription
  - **database/**: Database interfaces for Neo4j, vector DB, etc.
  - **api/**: FastAPI routes and endpoints
  - **scripts/**: Utility scripts for deployment and maintenance

- **backend/**: Original backend implementation (legacy)
- **frontend/**: User interface for the platform

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Neo4j (included in Docker setup)
- Redis (included in Docker setup)

### Quick Start with Docker

1. Clone the repository:
   ```
   git clone <repository-url>
   cd FinMate
   ```

2. Set up environment variables:
   ```
   cp backend_new/.env.example .env
   ```
   Edit the `.env` file to add your API keys and configuration.

3. Start the services:
   ```
   docker-compose up -d
   ```

4. Access the API at http://localhost:8000

### Manual Setup

See the [backend_new/README.md](backend_new/README.md) for detailed setup instructions.

## Documentation

- [API Documentation](http://localhost:8000/docs) (available after starting the service)
- [Deployment Guide](backend_new/DEPLOY.md)
- [Architecture Overview](backend_new/README.md)

## License

Proprietary - All rights reserved
