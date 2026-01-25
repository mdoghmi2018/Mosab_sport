from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole
from app.models.pt import PTRequest, PTRequestScope, PTRequestStatus

router = APIRouter()

class PTRequestCreateRequest(BaseModel):
    scope: PTRequestScope
    pt_user_id: Optional[UUID] = None
    match_id: Optional[UUID] = None
    reservation_id: Optional[UUID] = None
    details: Dict[str, Any]

class PTRequestResponse(BaseModel):
    id: str
    scope: str
    requester_user_id: str
    pt_user_id: Optional[str] = None
    status: str
    details: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/requests", response_model=PTRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_pt_request(
    request: PTRequestCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a PT request"""
    pt_request = PTRequest(
        scope=request.scope,
        requester_user_id=current_user.id,
        pt_user_id=request.pt_user_id,
        match_id=request.match_id,
        reservation_id=request.reservation_id,
        details=request.details,
        status=PTRequestStatus.OPEN
    )
    
    db.add(pt_request)
    db.commit()
    db.refresh(pt_request)
    
    return pt_request

@router.get("/inbox", response_model=List[PTRequestResponse])
async def get_pt_inbox(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get PT inbox - requests for current user as PT"""
    if current_user.role != UserRole.PERSONAL_TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only personal trainers can access inbox"
        )
    
    # Get requests where PT is assigned to current user OR unassigned (pt_user_id is None)
    from sqlalchemy import or_
    requests = db.query(PTRequest).filter(
        or_(
            PTRequest.pt_user_id == current_user.id,
            PTRequest.pt_user_id.is_(None)
        ),
        PTRequest.status == PTRequestStatus.OPEN
    ).order_by(PTRequest.created_at.desc()).all()
    
    return requests

@router.post("/requests/{request_id}/accept")
async def accept_pt_request(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a PT request"""
    if current_user.role != UserRole.PERSONAL_TRAINER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only personal trainers can accept requests"
        )
    
    from sqlalchemy import or_
    pt_request = db.query(PTRequest).filter(
        PTRequest.id == request_id,
        or_(
            PTRequest.pt_user_id == current_user.id,
            PTRequest.pt_user_id.is_(None)  # Can accept unassigned requests
        )
    ).first()
    
    if not pt_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found or already assigned to another PT"
        )
    
    # Assign PT if not already assigned
    if pt_request.pt_user_id is None:
        pt_request.pt_user_id = current_user.id
    
    pt_request.status = PTRequestStatus.ACCEPTED
    db.commit()
    
    return {"status": "accepted", "request_id": str(request_id)}

