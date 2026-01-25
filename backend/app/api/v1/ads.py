from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.ad import Advertiser, AdCreative, AdPlacement, AdCreativeStatus, AdPlacementSlot

router = APIRouter()

class AdCreativeSubmitRequest(BaseModel):
    advertiser_id: UUID
    media_url: str
    copy: Optional[str] = None

class AdPlacementCreateRequest(BaseModel):
    match_id: UUID
    slot: AdPlacementSlot
    creative_id: UUID

@router.post("/creatives/submit", status_code=status.HTTP_201_CREATED)
async def submit_ad_creative(
    request: AdCreativeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit an ad creative for approval"""
    advertiser = db.query(Advertiser).filter(Advertiser.id == request.advertiser_id).first()
    if not advertiser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Advertiser not found"
        )
    
    creative = AdCreative(
        advertiser_id=request.advertiser_id,
        media_url=request.media_url,
        copy=request.copy,
        status=AdCreativeStatus.SUBMITTED
    )
    
    db.add(creative)
    db.commit()
    db.refresh(creative)
    
    return {"creative_id": str(creative.id), "status": "submitted"}

@router.post("/placements", status_code=status.HTTP_201_CREATED)
async def create_ad_placement(
    request: AdPlacementCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an ad placement (only approved creatives)"""
    creative = db.query(AdCreative).filter(AdCreative.id == request.creative_id).first()
    if not creative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creative not found"
        )
    
    if creative.status != AdCreativeStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Creative must be approved before placement"
        )
    
    placement = AdPlacement(
        match_id=request.match_id,
        slot=request.slot,
        creative_id=request.creative_id
    )
    
    db.add(placement)
    db.commit()
    db.refresh(placement)
    
    return {"placement_id": str(placement.id), "status": "scheduled"}

