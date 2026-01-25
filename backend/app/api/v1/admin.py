from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole
from app.models.ad import AdCreative, AdCreativeStatus

router = APIRouter()

class RejectRequest(BaseModel):
    reason: str

@router.post("/ad-creatives/{creative_id}/approve")
async def approve_ad_creative(
    creative_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve an ad creative (super admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can approve ads"
        )
    
    creative = db.query(AdCreative).filter(AdCreative.id == creative_id).first()
    if not creative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creative not found"
        )
    
    creative.status = AdCreativeStatus.APPROVED
    creative.decided_by_user_id = current_user.id
    creative.decided_at = datetime.utcnow()
    
    db.commit()
    
    return {"status": "approved", "creative_id": str(creative_id)}

@router.post("/ad-creatives/{creative_id}/reject")
async def reject_ad_creative(
    creative_id: UUID,
    request: RejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject an ad creative (super admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can reject ads"
        )
    
    creative = db.query(AdCreative).filter(AdCreative.id == creative_id).first()
    if not creative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creative not found"
        )
    
    creative.status = AdCreativeStatus.REJECTED
    creative.decided_by_user_id = current_user.id
    creative.decided_at = datetime.utcnow()
    creative.rejection_reason = request.reason
    
    db.commit()
    
    return {"status": "rejected", "creative_id": str(creative_id)}

@router.post("/ad-creatives/{creative_id}/revoke")
async def revoke_ad_creative(
    creative_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke an approved ad creative (super admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admin can revoke ads"
        )
    
    creative = db.query(AdCreative).filter(AdCreative.id == creative_id).first()
    if not creative:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creative not found"
        )
    
    creative.status = AdCreativeStatus.REVOKED
    creative.decided_by_user_id = current_user.id
    creative.decided_at = datetime.utcnow()
    
    # All placements with this creative will be disabled
    # (handled by application logic when rendering)
    
    db.commit()
    
    return {"status": "revoked", "creative_id": str(creative_id)}

