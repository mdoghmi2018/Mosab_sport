from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.api.v1.router import api_router
from app.middleware.rate_limit import RateLimitMiddleware
import logging
import time

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mosab Sport API",
    description="Sports platform for booking, match management, and reporting",
    version="1.0.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if settings.is_development else None
)

# CORS middleware - restricted in production
allowed_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"] if settings.is_production else ["*"]
allowed_headers = ["Content-Type", "Authorization", "Idempotency-Key"] if settings.is_production else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=allowed_methods,
    allow_headers=allowed_headers,
    expose_headers=["X-Request-ID"],
)

# Add rate limiting middleware
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request ID and process time"""
    start_time = time.time()
    request_id = request.headers.get("X-Request-ID", f"req-{int(time.time() * 1000)}")
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors without exposing internal details"""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    # In production, don't expose error details
    detail = "Internal server error" if settings.is_production else str(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail}
    )

@app.get("/health")
async def health_check():
    """Health check endpoint with dependency checks"""
    from app.core.database import engine
    from app.core.redis_client import redis_client
    
    health_status = {
        "status": "healthy",
        "service": "mosab-sport-api",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "checks": {}
    }
    
    # Check database
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)

@app.get("/")
async def root():
    return {
        "message": "Mosab Sport API",
        "docs": "/docs",
        "health": "/health"
    }

