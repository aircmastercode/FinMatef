# FinMate API Documentation

## Overview
This document provides detailed information about the FinMate API endpoints, request/response formats, and authentication requirements.

## Authentication
All API endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Endpoints

### Chat Endpoints
- POST /api/chat/send
- GET /api/chat/history
- POST /api/chat/voice

### Admin Endpoints
- POST /api/admin/upload
- GET /api/admin/documents
- PUT /api/admin/documents/{id}

### File Endpoints
- POST /api/files/upload
- GET /api/files/{id}
- DELETE /api/files/{id}

## Response Formats
All responses follow a standard format:
```json
{
  "status": "success|error",
  "data": {},
  "message": "Optional message"
}
```

## Error Handling
Standard HTTP status codes are used:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 500: Internal Server Error 