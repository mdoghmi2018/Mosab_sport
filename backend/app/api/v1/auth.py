from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from app.core.database import get_db
from app.core.redis_client import get_redis
from app.core.security import create_access_token, generate_otp, decode_access_token
from app.models.user import User
from datetime import timedelta
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()

class AuthStartRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class AuthVerifyRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    otp: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: str

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    user_id_str: str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user

@router.post("/start")
async def auth_start(
    request: AuthStartRequest,
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    """Start authentication - send OTP"""
    if not request.phone and not request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either phone or email is required"
        )
    
    identifier = request.phone or request.email
    otp = generate_otp()
    
    # Store OTP in Redis with 10 minute expiry
    redis.setex(f"otp:{identifier}", 600, otp)
    
    # In development, log OTP for testing
    if settings.is_development:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"OTP for {identifier}: {otp}")
    
    # TODO: Send OTP via SMS/Email service
    
    return {"message": "OTP sent", "identifier": identifier}

@router.post("/dev-otp")
async def dev_get_otp(
    request: AuthStartRequest,
    redis = Depends(get_redis)
):
    """Development endpoint to get OTP (only in dev mode)"""
    if settings.is_production:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in development"
        )
    
    if not request.phone and not request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either phone or email is required"
        )
    
    identifier = request.phone or request.email
    otp = redis.get(f"otp:{identifier}")
    
    if not otp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No OTP found. Call /auth/start first."
        )
    
    return {"otp": otp, "identifier": identifier}

@router.post("/verify")
async def auth_verify(
    request: AuthVerifyRequest,
    db: Session = Depends(get_db),
    redis = Depends(get_redis)
):
    """Verify OTP and return JWT token"""
    if not request.phone and not request.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either phone or email is required"
        )
    
    identifier = request.phone or request.email
    stored_otp = redis.get(f"otp:{identifier}")
    
    if not stored_otp or stored_otp != request.otp:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid OTP"
        )
    
    # Get or create user
    if request.phone:
        user = db.query(User).filter(User.phone == request.phone).first()
        if not user:
            user = User(phone=request.phone, name="", verified_phone=True)
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.verified_phone = True
            db.commit()
    else:
        user = db.query(User).filter(User.email == request.email).first()
        if not user:
            user = User(email=request.email, name="", verified_email=True)
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.verified_email = True
            db.commit()
    
    # Delete OTP
    redis.delete(f"otp:{identifier}")
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return AuthResponse(
        access_token=access_token,
        user_id=str(user.id),
        role=user.role.value
    )

