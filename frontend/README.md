# FinMate Frontend

This is the frontend application for FinMate, a conversational AI platform for LenDen Club.

## Features

- User chat interface with text and voice input
- Session management for conversations
- Admin panel for document upload and knowledge management
- Escalation management system

## Getting Started

### Prerequisites

- Node.js 16.x or higher
- npm 8.x or higher

### Installation

1. Install dependencies:

```bash
npm install
```

2. Create a `.env` file in the frontend directory with the following content:

```
REACT_APP_API_URL=http://localhost:8000
```

### Development

To start the development server:

```bash
npm start
```

The application will be available at [http://localhost:3000](http://localhost:3000).

### Building for Production

To build the application for production:

```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Project Structure

- `src/components/` - Reusable UI components
- `src/pages/` - Page components
- `src/services/` - API services and utilities
- `src/utils/` - Helper functions
- `src/assets/` - Static assets

## Available Routes

- `/user` - User chat interface
- `/admin` - Admin panel for document management and escalations

## Docker

A Dockerfile is provided to containerize the frontend application. To build and run:

```bash
# Build the Docker image
docker build -t finmate-frontend .

# Run the container
docker run -p 80:80 finmate-frontend
```

## Integration with Backend

The frontend is configured to communicate with the backend API at the URL specified in the `REACT_APP_API_URL` environment variable. Make sure the backend is running and accessible at this URL. 