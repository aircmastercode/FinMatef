"""
FinMate AI Platform - Main Application Entry Point

This module initializes the FastAPI application, sets up middleware,
and includes all API routes.
"""
import logging
import os
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.admin import router as admin_router
from api.user import router as user_router
from config import settings
from dependencies import get_conductor_agent

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="FinMate AI Platform",
    description="A conversational AI platform for LenDen Club",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "message": str(e)},
        )

# Include routers
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(user_router, prefix="/user", tags=["user"])

@app.get("/", tags=["system"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint that returns basic API information.
    """
    return {
        "name": "FinMate AI Platform",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/health", tags=["system"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint that verifies system components.
    """
    # In a real implementation, this would check database connections,
    # external services, etc.
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "healthy",
            "database": "healthy",  # Would be checked in a real implementation
            "llm_service": "healthy",  # Would be checked in a real implementation
        },
        "environment": settings.environment,
    }
    
    return health_status

@app.get("/system/info", tags=["system"])
async def system_info() -> Dict[str, Any]:
    """
    System information endpoint that returns configuration details.
    """
    return {
        "environment": settings.environment,
        "log_level": settings.log_level,
        "model_name": settings.model_name,
        "version": "1.0.0",
    }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting FinMate AI Platform")
    
    try:
        # Create directories if they don't exist
        os.makedirs(settings.upload_dir, exist_ok=True)
        os.makedirs(settings.processed_dir, exist_ok=True)
        os.makedirs(settings.temp_dir, exist_ok=True)
        
        logger.info("Successfully initialized all services")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down FinMate AI Platform")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    ) 