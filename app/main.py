"""
AyTiX Marketplace API
Production-ready FastAPI backend
"""
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.database import engine, Base
import logging
import os
import time

# Logger setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import routers
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.products.router import router as products_router
from app.categories.router import router as categories_router
from app.categories.project_router import router as project_categories_router
from app.orders.router import router as orders_router
from app.admin.router import router as admin_router
from app.stats.router import router as stats_router
from app.projects.router import router as projects_router
from app.uploads.router import router as uploads_router
from app.content.router import router as content_router
from app.messages.router import router as messages_router
from app.partners.router import router as partners_router
from app.integrations.router import router as integrations_router
from app.ai_features.router import router as ai_features_router
from app.translate.router import router as translate_router

# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AyTiX Marketplace - Professional API for Projects and Services",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Custom CORS Middleware for better control
class CORSMiddlewareCustom(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Handle preflight OPTIONS requests
        if request.method == "OPTIONS":
            response = Response(status_code=204)
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Max-Age"] = "600"
            return response

        # Process the request
        response = await call_next(request)

        # Add CORS headers to all responses
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With, Accept, Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"

        return response


# Add custom CORS middleware first (for handling OPTIONS and adding headers)
app.add_middleware(CORSMiddlewareCustom)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Standard CORS middleware as backup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Total-Count", "*"],
    max_age=600
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time * 1000, 2)) + "ms"
    return response


# Upload directories setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(os.path.dirname(BASE_DIR), "uploads")
IMAGES_DIR = os.path.join(UPLOAD_DIR, "images")
VIDEOS_DIR = os.path.join(UPLOAD_DIR, "videos")

# Create directories
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)
logger.info(f"Upload directory: {UPLOAD_DIR}")

# Mount static files
try:
    app.mount("/uploads/images", StaticFiles(directory=IMAGES_DIR), name="images")
    app.mount("/uploads/videos", StaticFiles(directory=VIDEOS_DIR), name="videos")
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

# Include routers
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(products_router, prefix=settings.API_V1_PREFIX)
app.include_router(categories_router, prefix=settings.API_V1_PREFIX)
app.include_router(project_categories_router, prefix=settings.API_V1_PREFIX)
app.include_router(orders_router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_router, prefix=settings.API_V1_PREFIX)
app.include_router(stats_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(uploads_router, prefix=settings.API_V1_PREFIX)
app.include_router(content_router, prefix=settings.API_V1_PREFIX)
app.include_router(messages_router, prefix=settings.API_V1_PREFIX)
app.include_router(partners_router, prefix=settings.API_V1_PREFIX)
app.include_router(integrations_router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_features_router, prefix=settings.API_V1_PREFIX)
app.include_router(translate_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "message": "AyTiX Marketplace API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health")
def health():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": time.time()
    }


# API v1 health check
@app.get("/api/v1/health")
def api_health():
    """API v1 health check endpoint."""
    return {"status": "healthy", "version": "2.0.0", "timestamp": time.time()}


# HTTP Exception handler
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


# Validation Exception handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


# Global Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with CORS support."""
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*"
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Log startup information."""
    logger.info("=" * 50)
    logger.info("AyTiX Marketplace API starting...")
    logger.info(f"Version: 2.0.0")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"API prefix: {settings.API_V1_PREFIX}")
    logger.info(f"Upload directory: {UPLOAD_DIR}")
    logger.info(f"API docs available at /docs")
    logger.info("=" * 50)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("AyTiX Marketplace API shutting down...")
