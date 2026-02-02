from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole
from app.models.addon import Addon, AddonCategory, AddonStatus

router = APIRouter()

class AddonResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: str
    price_cents: int
    currency: str
    status: str
    is_custom: bool
    metadata_json: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True

class AddonCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: AddonCategory
    price_cents: int
    currency: str = "USD"
    is_custom: bool = False
    metadata_json: Optional[dict] = None

class AddonUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[AddonCategory] = None
    price_cents: Optional[int] = None
    currency: Optional[str] = None
    status: Optional[AddonStatus] = None
    is_custom: Optional[bool] = None
    metadata_json: Optional[dict] = None

@router.get("/", response_model=List[AddonResponse])
async def list_addons(
    category: Optional[AddonCategory] = None,
    status: Optional[AddonStatus] = None,
    db: Session = Depends(get_db)
):
    """List all add-ons with optional filters"""
    query = db.query(Addon)
    
    if category:
        query = query.filter(Addon.category == category)
    
    if status:
        query = query.filter(Addon.status == status)
    else:
        # By default, only show active add-ons
        query = query.filter(Addon.status == AddonStatus.ACTIVE)
    
    addons = query.order_by(Addon.name).all()
    return addons

@router.get("/{addon_id}", response_model=AddonResponse)
async def get_addon(
    addon_id: UUID,
    db: Session = Depends(get_db)
):
    """Get addon details"""
    addon = db.query(Addon).filter(Addon.id == addon_id).first()
    
    if not addon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Addon not found"
        )
    
    return addon

@router.post("/", response_model=AddonResponse, status_code=status.HTTP_201_CREATED)
async def create_addon(
    request: AddonCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new addon (admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create addons"
        )
    
    # Check if addon with same name exists
    existing = db.query(Addon).filter(Addon.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Addon with this name already exists"
        )
    
    addon = Addon(
        name=request.name,
        description=request.description,
        category=request.category,
        price_cents=request.price_cents,
        currency=request.currency,
        is_custom=request.is_custom,
        metadata_json=request.metadata_json,
        status=AddonStatus.ACTIVE
    )
    
    db.add(addon)
    db.commit()
    db.refresh(addon)
    
    return addon

@router.patch("/{addon_id}", response_model=AddonResponse)
async def update_addon(
    addon_id: UUID,
    request: AddonUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update addon (admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update addons"
        )
    
    addon = db.query(Addon).filter(Addon.id == addon_id).first()
    
    if not addon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Addon not found"
        )
    
    # Update fields
    if request.name is not None:
        # Check if name is already taken by another addon
        existing = db.query(Addon).filter(
            Addon.name == request.name,
            Addon.id != addon_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Addon with this name already exists"
            )
        addon.name = request.name
    
    if request.description is not None:
        addon.description = request.description
    if request.category is not None:
        addon.category = request.category
    if request.price_cents is not None:
        addon.price_cents = request.price_cents
    if request.currency is not None:
        addon.currency = request.currency
    if request.status is not None:
        addon.status = request.status
    if request.is_custom is not None:
        addon.is_custom = request.is_custom
    if request.metadata_json is not None:
        addon.metadata_json = request.metadata_json
    
    db.commit()
    db.refresh(addon)
    
    return addon

