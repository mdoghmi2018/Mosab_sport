from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.match import Match
from app.models.award import MatchAward, AwardKind

router = APIRouter()

class AwardCreateRequest(BaseModel):
    kind: AwardKind
    winner_ref: str  # player_id or event_id

class AwardResponse(BaseModel):
    id: str
    match_id: str
    kind: str
    winner_ref: str
    decided_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/matches/{match_id}/awards", response_model=AwardResponse, status_code=status.HTTP_201_CREATED)
async def create_award(
    match_id: UUID,
    request: AwardCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an award for a match"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Check if award of this kind already exists
    existing = db.query(MatchAward).filter(
        MatchAward.match_id == match_id,
        MatchAward.kind == request.kind
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Award of kind {request.kind.value} already exists for this match"
        )
    
    award = MatchAward(
        match_id=match_id,
        kind=request.kind,
        winner_ref=request.winner_ref,
        decided_by_user_id=current_user.id
    )
    
    db.add(award)
    db.commit()
    db.refresh(award)
    
    return award

@router.get("/matches/{match_id}/awards", response_model=List[AwardResponse])
async def get_match_awards(
    match_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all awards for a match"""
    awards = db.query(MatchAward).filter(
        MatchAward.match_id == match_id
    ).all()
    
    return awards

