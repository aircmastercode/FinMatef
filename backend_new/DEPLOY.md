# Deployment Guide for FinMate AI Platform

This guide describes how to deploy the FinMate AI Platform using Docker and Docker Compose.

## Prerequisites

- Docker and Docker Compose installed on your system
- OpenAI API key
- Cognee API key (if using Cognee integration)
- Search API key (if using web search capabilities)

## Configuration

1. Clone the repository (if you haven't already):
   ```
   git clone <repository-url>
   cd FinMate
   ```

2. Create a `.env` file in the project root with your configuration:
   ```
   cp backend_new/.env.example .env
   ```

3. Edit the `.env` file and fill in your API keys and configuration details:
   ```
   nano .env
   ```

## Running with Docker Compose

1. Start all services:
   ```
   docker-compose up -d
   ```

2. Check service status:
   ```
   docker-compose ps
   ```

3. View logs:
   ```
   docker-compose logs -f
   ```

4. Stop services:
   ```
   docker-compose down
   ```

## Using the Run Script

For convenience, you can use the provided script to set up and run the services:

```
cd backend_new/scripts
./run_services.sh
```

This script will:
1. Create a `.env` file if it doesn't exist
2. Create the necessary directories
3. Start the Docker containers
4. Display service status

## Accessing Services

- **API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Neo4j Browser:** http://localhost:7474 (username: neo4j, password: from .env)

## Production Deployment Considerations

For production deployment, consider the following:

1. Use a reverse proxy (like Nginx) in front of the API
2. Set up SSL certificates
3. Configure proper authentication
4. Use managed database services instead of containers
5. Set up monitoring and logging
6. Configure container restart policies
7. Use container orchestration (Kubernetes) for scaling

## Troubleshooting

- If you encounter port conflicts, edit the `docker-compose.yml` file to map services to different host ports
- Check logs for specific container issues: `docker-compose logs <service-name>`
- Ensure all API keys are correctly set in the `.env` file
- Verify network connectivity between containers if using external services 