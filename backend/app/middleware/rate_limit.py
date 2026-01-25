from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.redis_client import get_redis
from app.core.config import settings
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting if disabled
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Only rate limit auth endpoints
        if request.url.path.startswith("/api/v1/auth"):
            redis = get_redis()
            client_ip = request.client.host if request.client else "unknown"
            endpoint = request.url.path
            
            # Create rate limit key
            key = f"rate_limit:{client_ip}:{endpoint}"
            
            # Get current count
            current = redis.get(key)
            
            if current and int(current) >= settings.RATE_LIMIT_PER_MINUTE:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
            
            # Increment counter
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, 60)  # 1 minute window
            pipe.execute()
        
        return await call_next(request)

