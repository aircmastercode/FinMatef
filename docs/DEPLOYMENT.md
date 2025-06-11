# FinMate Deployment Guide

## Prerequisites
- Docker and Docker Compose
- Node.js 18+
- Python 3.9+
- Neo4j Database
- OpenAI API Key

## Environment Setup
1. Copy `.env.example` to `.env` in both frontend and backend directories
2. Update environment variables with your configuration
3. Install dependencies:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt

   # Frontend
   cd frontend
   npm install
   ```

## Development Deployment
1. Start the development environment:
   ```bash
   docker-compose -f docker-compose.dev.yml up
   ```

2. Access the applications:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Production Deployment
1. Build the production images:
   ```bash
   docker-compose build
   ```

2. Start the production environment:
   ```bash
   docker-compose up -d
   ```

## Database Setup
1. Install Neo4j
2. Create a new database
3. Update connection details in `.env`
4. Run database migrations

## Monitoring
- Application logs: `docker-compose logs -f`
- Database monitoring: Neo4j Browser
- API metrics: Prometheus/Grafana

## Backup and Recovery
- Regular database backups
- Configuration backups
- Disaster recovery procedures 