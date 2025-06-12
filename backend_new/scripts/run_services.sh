#!/bin/bash

# Ensure the script directory exists
mkdir -p $(dirname "$0")

# Create the .env file if it doesn't exist
if [ ! -f ../.env ]; then
    echo "Creating .env file..."
    cat > ../.env << EOL
# API Keys
OPENAI_API_KEY=your_openai_api_key
COGNEE_API_KEY=your_cognee_api_key
COGNEE_API_URL=https://api.cognee.com/v1
SEARCH_API_KEY=your_search_api_key
SEARCH_ENGINE_ID=your_search_engine_id

# Database Connections
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
VECTOR_DB_URI=your_vector_db_uri
VECTOR_DB_API_KEY=your_vector_db_api_key

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
MAX_TOKENS=4096
MODEL_NAME=gpt-3.5-turbo
EOL
    echo "Please update the .env file with your API keys and configuration before continuing."
    exit 1
else
    echo ".env file exists, continuing with setup..."
fi

# Create data directory if it doesn't exist
mkdir -p ../data

# Start the services
cd ..
docker-compose up -d

# Display service status
docker-compose ps

echo "Services started successfully!"
echo "API is accessible at http://localhost:8000"
echo "Neo4j browser is accessible at http://localhost:7474 (username: neo4j, check .env for password)" 