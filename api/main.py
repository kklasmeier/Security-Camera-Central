"""
Security Camera Central Server API
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from api.config import settings
from api.database import check_database_connection
from api.routes import health

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events for the application
    """
    # Startup
    logger.info("Starting Security Camera Central Server API")
    logger.info(f"API listening on {settings.api_host}:{settings.api_port}")
    
    # Check database connection on startup
    if check_database_connection():
        logger.info("Database connection verified")
    else:
        logger.error("Database connection failed - API may not work correctly")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Security Camera Central Server API")


# Create FastAPI application
app = FastAPI(
    title="Security Camera Central Server API",
    description="REST API for multi-camera security system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS (allow web UI to call API from browser)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api/v1 prefix
app.include_router(health.router, prefix="/api/v1", tags=["Health"])

# Future routers will be added here in subsequent sessions:
# app.include_router(cameras.router, prefix="/api/v1", tags=["Cameras"])
# app.include_router(events.router, prefix="/api/v1", tags=["Events"])
# app.include_router(logs.router, prefix="/api/v1", tags=["Logs"])


@app.get("/")
def root():
    """
    Root endpoint - provides API information
    """
    return {
        "message": "Security Camera Central Server API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/v1/health"
    }