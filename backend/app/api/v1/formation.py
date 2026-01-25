from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.formation import Squad, SquadMember, Formation, PlayerProfile
from app.models.match import Match
import secrets

router = APIRouter()

class SquadCreateRequest(BaseModel):
    team_name: str
    sport: str

class FormationCreateRequest(BaseModel):
    match_id: Optional[UUID] = None
    squad_id: Optional[UUID] = None
    shape: str  # "4-4-2", "3-5-2", etc
    positions_json: Dict[str, Any]

class FormationResponse(BaseModel):
    id: str
    match_id: Optional[str] = None
    squad_id: Optional[str] = None
    shape: str
    positions_json: Dict[str, Any]
    share_token: str
    
    class Config:
        from_attributes = True

@router.post("/squads", status_code=status.HTTP_201_CREATED)
async def create_squad(
    request: SquadCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a squad"""
    squad = Squad(
        team_name=request.team_name,
        sport=request.sport,
        owner_user_id=current_user.id
    )
    
    db.add(squad)
    db.commit()
    db.refresh(squad)
    
    return {"squad_id": str(squad.id), "team_name": squad.team_name}

@router.post("/squads/import/whatsapp")
async def import_squad_from_whatsapp(
    whatsapp_text: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import squad from WhatsApp message (AI parsing)"""
    # TODO: Implement AI parsing of WhatsApp message
    # For now, return placeholder
    return {"message": "WhatsApp import not yet implemented", "text": whatsapp_text[:100]}

@router.post("/matches/{match_id}/formation", response_model=FormationResponse, status_code=status.HTTP_201_CREATED)
async def create_match_formation(
    match_id: UUID,
    request: FormationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create formation for a match"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    share_token = secrets.token_urlsafe(32)
    
    formation = Formation(
        match_id=match_id,
        squad_id=request.squad_id,
        shape=request.shape,
        positions_json=request.positions_json,
        share_token=share_token,
        share_permission="view"
    )
    
    db.add(formation)
    db.commit()
    db.refresh(formation)
    
    return formation

@router.get("/formations/{share_token}", response_model=FormationResponse)
async def get_formation_by_token(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Get formation by share token (public access)"""
    formation = db.query(Formation).filter(
        Formation.share_token == share_token
    ).first()
    
    if not formation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formation not found"
        )
    
    return formation

