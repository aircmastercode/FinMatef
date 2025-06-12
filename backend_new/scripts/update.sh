#!/bin/bash

# Navigate to project root
cd "$(dirname "$0")/.."

# Pull latest changes
echo "Pulling latest changes..."
git pull

# Rebuild containers with the latest code
echo "Rebuilding containers..."
docker-compose down
docker-compose build
docker-compose up -d

# Show status
echo "Services started with updated code."
docker-compose ps

echo "Update completed successfully!"
echo "API is accessible at http://localhost:8000" 