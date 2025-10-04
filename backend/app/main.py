from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
import time
import hashlib
import json
from typing import Dict, Any
import redis
from .core.config import settings
from .database import engine
from .models.models import Base
from .api import auth, resumes, jobs

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize Redis for idempotency
try:
    redis_client = redis.from_url(settings.redis_url)
    redis_client.ping()
except:
    redis_client = None

# In-memory storage for idempotency if Redis is not available
idempotency_cache: Dict[str, Dict[str, Any]] = {}

# Rate limiting storage
rate_limit_storage: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="ResumeRAG API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api", tags=["authentication"])
app.include_router(resumes.router, prefix="/api", tags=["resumes"])
app.include_router(jobs.router, prefix="/api", tags=["jobs"])


@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware - 60 requests per minute per user."""
    # Get user identifier (IP address for now, could be user ID if authenticated)
    user_id = request.client.host
    
    current_time = time.time()
    minute_window = 60
    
    # Clean old entries
    if user_id in rate_limit_storage:
        rate_limit_storage[user_id] = {
            k: v for k, v in rate_limit_storage[user_id].items()
            if current_time - v < minute_window
        }
    else:
        rate_limit_storage[user_id] = {}
    
    # Count requests in current window
    request_count = len(rate_limit_storage[user_id])
    
    if request_count >= 60:
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "RATE_LIMIT"}}
        )
    
    # Add current request
    rate_limit_storage[user_id][str(current_time)] = current_time
    
    response = await call_next(request)
    return response


@app.middleware("http")
async def idempotency_middleware(request: Request, call_next):
    """Idempotency middleware for POST requests."""
    if request.method != "POST":
        return await call_next(request)
    
    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        return await call_next(request)
    
    # Create cache key
    cache_key = f"idempotency:{idempotency_key}"
    
    # Check if we have a cached response
    cached_response = None
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                cached_response = json.loads(cached_data)
        except:
            pass
    
    if not cached_response and cache_key in idempotency_cache:
        cached_response = idempotency_cache[cache_key]
    
    if cached_response:
        return JSONResponse(
            status_code=cached_response["status_code"],
            content=cached_response["content"],
            headers=cached_response.get("headers", {})
        )
    
    # Process request
    response = await call_next(request)
    
    # Cache response
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    
    response_data = {
        "status_code": response.status_code,
        "content": json.loads(response_body.decode()) if response_body else {},
        "headers": dict(response.headers)
    }
    
    if redis_client:
        try:
            redis_client.setex(cache_key, 3600, json.dumps(response_data))  # Cache for 1 hour
        except:
            pass
    
    idempotency_cache[cache_key] = response_data
    
    # Return response
    return JSONResponse(
        status_code=response.status_code,
        content=response_data["content"],
        headers=response_data["headers"]
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with uniform error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.detail.get("code", "HTTP_ERROR") if isinstance(exc.detail, dict) else "HTTP_ERROR",
                "field": exc.detail.get("field") if isinstance(exc.detail, dict) else None,
                "message": exc.detail.get("message", str(exc.detail)) if isinstance(exc.detail, dict) else str(exc.detail)
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with uniform error format."""
    errors = exc.errors()
    if errors:
        error = errors[0]
        field = ".".join(str(loc) for loc in error["loc"][1:])  # Skip "body" prefix
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "field": field,
                    "message": error["msg"]
                }
            }
        )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with uniform error format."""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "ResumeRAG API is running"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
