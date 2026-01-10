"""
Vastgoed API - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI
from app.models.historie_setup import setup_historie_listeners  # Historie toevoeging
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.endpoints.projectfase_endpoints import router as projectfase_router

from app.core.config import settings
from app.api.api import api_router
from app.db.init_db import init_db
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events for the application
    """
    # Startup: Initialize database
    print("🚀 Starting up...")
    init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Vastgoed API",
    description="REST API voor vastgoed proces- en contractbeheersing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Setup historie listeners 
setup_historie_listeners()

# CORS middleware - CRITICAL!
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",  # Vue app port
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Include API router
app.include_router(api_router, prefix="/api/v1")
app.include_router(projectfase_router, prefix="/api/v1")


@app.get("/")
async def root():
    """
    Root endpoint - health check
    """
    return {
        "message": "Vastgoed API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload bij code changes
        log_level="info"
    )
