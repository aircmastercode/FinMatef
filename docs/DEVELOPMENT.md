# FinMate Development Guide

## Development Environment Setup

### Backend Setup
1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Frontend Setup
1. Install Node.js dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

## Development Workflow

### Code Style
- Backend: Follow PEP 8 guidelines
- Frontend: Use ESLint and Prettier
- TypeScript: Enable strict mode

### Testing
1. Backend tests:
   ```bash
   cd backend
   pytest
   ```

2. Frontend tests:
   ```bash
   cd frontend
   npm test
   ```

### Git Workflow
1. Create feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Commit changes:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

3. Push and create pull request

## Debugging

### Backend Debugging
- Use FastAPI debug mode
- Enable logging
- Use debugger in IDE

### Frontend Debugging
- React Developer Tools
- Redux DevTools
- Browser Developer Tools

## Common Issues
- Database connection issues
- CORS configuration
- Environment variables
- Dependency conflicts 