FinMate Project Structure

Root Directory Structure
text
finmate/
├── backend/
│   ├── src/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── main_agent.py          # Main orchestrator agent
│   │   │   ├── file_processing_agent.py    # Handles admin uploads
│   │   │   ├── query_processing_agent.py   # Analyzes user queries
│   │   │   ├── loan_agent.py          # Loan-specific queries
│   │   │   ├── account_agent.py       # Account management
│   │   │   ├── policy_agent.py        # Policy information
│   │   │   ├── database_agent.py      # Database retrieval
│   │   │   ├── response_synthesis_agent.py  # Combines responses
│   │   │   ├── web_search_agent.py    # External search
│   │   │   └── email_agent.py         # Escalation handling
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── admin.py           # Admin endpoints
│   │   │   │   ├── chat.py            # Chat endpoints
│   │   │   │   ├── voice.py           # Voice processing
│   │   │   │   └── files.py           # File upload
│   │   │   └── dependencies.py        # Shared dependencies
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py              # Configuration settings
│   │   │   ├── security.py            # Security utilities
│   │   │   ├── database.py            # Database connections
│   │   │   └── exceptions.py          # Custom exceptions
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── voice_service.py       # Whisper ASR integration
│   │   │   ├── email_service.py       # Email functionality
│   │   │   ├── file_service.py        # File processing
│   │   │   ├── search_service.py      # Web search
│   │   │   └── cognee_service.py      # Cognee integration
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py             # Pydantic models
│   │   │   ├── database_models.py     # Database models
│   │   │   └── enums.py               # Enumerations
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── helpers.py             # Utility functions
│   │   │   ├── validators.py          # Input validation
│   │   │   └── formatters.py          # Response formatting
│   │   └── main.py                    # FastAPI application entry
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_agents/
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── conftest.py
│   ├── requirements.txt               # Python dependencies
│   ├── Dockerfile                     # Backend container
│   └── .env.example                   # Environment template
├── frontend/
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── src/
│   │   ├── components/
│   │   │   ├── admin/
│   │   │   │   ├── AdminDashboard.tsx
│   │   │   │   ├── FileUpload.tsx
│   │   │   │   └── DataManagement.tsx
│   │   │   ├── chat/
│   │   │   │   ├── ChatInterface.tsx
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── VoiceInput.tsx
│   │   │   │   └── TypingIndicator.tsx
│   │   │   ├── common/
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Button.tsx
│   │   │   │   └── Modal.tsx
│   │   │   └── auth/
│   │   │       ├── Login.tsx
│   │   │       └── ProtectedRoute.tsx
│   │   ├── hooks/
│   │   │   ├── useChat.ts             # Chat functionality
│   │   │   ├── useVoice.ts            # Voice recording
│   │   │   ├── useWebSocket.ts        # Real-time communication
│   │   │   └── useAuth.ts             # Authentication
│   │   ├── services/
│   │   │   ├── api.ts                 # API client
│   │   │   ├── websocket.ts           # WebSocket service
│   │   │   └── storage.ts             # Local storage
│   │   ├── store/
│   │   │   ├── index.ts               # Redux/Zustand store
│   │   │   ├── chatSlice.ts           # Chat state
│   │   │   └── authSlice.ts           # Auth state
│   │   ├── types/
│   │   │   ├── api.ts                 # API types
│   │   │   ├── chat.ts                # Chat types
│   │   │   └── auth.ts                # Auth types
│   │   ├── utils/
│   │   │   ├── constants.ts           # Constants
│   │   │   ├── formatters.ts          # Formatting utilities
│   │   │   └── validators.ts          # Input validation
│   │   ├── App.tsx                    # Main app component
│   │   ├── index.tsx                  # Entry point
│   │   └── index.css                  # Global styles
│   ├── package.json                   # Node dependencies
│   ├── tsconfig.json                  # TypeScript config
│   ├── tailwind.config.js             # Tailwind CSS config
│   └── Dockerfile                     # Frontend container
├── docker-compose.yml                 # Multi-container orchestration
├── docker-compose.dev.yml             # Development environment
├── README.md                          # Project documentation
├── .gitignore                         # Git ignore rules
├── .env.example                       # Environment variables template
└── docs/
    ├── API.md                         # API documentation
    ├── DEPLOYMENT.md                  # Deployment guide
    ├── ARCHITECTURE.md                # System architecture
    └── DEVELOPMENT.md                 # Development setup
Key Configuration Files
Backend Requirements (requirements.txt)
text
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
python-dotenv==1.0.0
openai==1.3.0
whisper==1.1.10
neo4j==5.15.0
langchain==0.0.350
langchain-neo4j==0.0.5
cognee==0.1.15
fastapi-mail==1.4.1
httpx==0.25.0
websockets==12.0
pytest==7.4.0
pytest-asyncio==0.21.0
Frontend Dependencies (package.json)
json
{
  "name": "finmate-frontend",
  "version": "1.0.0",
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.2.0",
    "axios": "^1.6.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "tailwindcss": "^3.3.0",
    "react-router-dom": "^6.8.0",
    "zustand": "^4.4.0",
    "react-query": "^3.39.0"
  }
}
Environment Variables (.env)
text
# Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Email Configuration
MAIL_USERNAME=your_email@company.com
MAIL_PASSWORD=your_app_password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
EMPLOYEE_EMAIL=support@company.com

# Security
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External APIs
SEARCH_API_KEY=your_search_api_key
SEARCH_API_URL=https://api.searchapi.io/api/v1/search

# Development
DEBUG=True
ENVIRONMENT=development
Database Schema Design
Neo4j Graph Schema
text
# User Nodes
(:User {id, name, email, created_at, session_id})

# Chat Nodes
(:ChatSession {id, user_id, created_at, status})
(:Message {id, session_id, content, type, timestamp, intent})

# Knowledge Nodes
(:Document {id, title, content, type, uploaded_at})
(:FAQ {id, question, answer, category, created_at})
(:Policy {id, name, content, effective_date})
(:Loan {id, type, details, requirements})

# Relationships
(:User)-[:HAS_SESSION]->(:ChatSession)
(:ChatSession)-[:CONTAINS]->(:Message)
(:Message)-[:RELATES_TO]->(:Document)
(:Document)-[:BELONGS_TO]->(:Category)
Agent Design Patterns
Main Agent (Orchestrator)
Receives all requests from main.py
Analyzes request type and intent
Routes to appropriate specialist agents
Manages agent communication
Handles error scenarios and fallbacks
Specialist Agents
Independent, focused functionality
Clear input/output interfaces
Database access through Database Agent
Stateless design for scalability
Error handling and logging
Database Agent
Centralized database access
Optimized queries for different data types
Caching mechanisms
Connection pooling
Data validation
