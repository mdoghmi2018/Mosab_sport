from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole
from app.models.match import Match, MatchStatus, RefereeAssignment, RefereeAssignmentStatus, MatchEvent
from app.models.booking import Reservation
from app.models.venue import Slot

router = APIRouter()

class MatchResponse(BaseModel):
    id: str
    reservation_id: str
    sport: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class RefereeOfferRequest(BaseModel):
    referee_user_id: UUID

class MatchEventCreateRequest(BaseModel):
    seq: int
    ts: datetime
    type: str
    payload: Dict[str, Any]

class MatchEventResponse(BaseModel):
    id: str
    match_id: str
    seq: int
    ts: datetime
    type: str
    payload: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/from-reservation/{reservation_id}", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match_from_reservation(
    reservation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a match from a paid reservation"""
    reservation = db.query(Reservation).options(
        joinedload(Reservation.slot).joinedload(Slot.court)
    ).filter(Reservation.id == reservation_id).first()
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    if reservation.status != ReservationStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation must be paid"
        )
    
    # Check if match already exists
    existing_match = db.query(Match).filter(Match.reservation_id == reservation_id).first()
    if existing_match:
        return existing_match
    
    match = Match(
        reservation_id=reservation_id,
        sport=reservation.slot.court.sport,
        status=MatchStatus.SCHEDULED
    )
    
    db.add(match)
    db.commit()
    db.refresh(match)
    
    return match

@router.post("/{match_id}/referee/offer", response_model=dict)
async def offer_referee(
    match_id: UUID,
    request: RefereeOfferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Offer referee assignment to a match"""
    # Only organizers or admins can offer referee assignments
    if current_user.role not in [UserRole.ORGANIZER, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organizers or admins can offer referee assignments"
        )
    
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Check if referee user exists and has referee role
    referee = db.query(User).filter(
        User.id == request.referee_user_id,
        User.role == UserRole.REFEREE
    ).first()
    
    if not referee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referee not found"
        )
    
    # Create or update assignment
    assignment = db.query(RefereeAssignment).filter(
        RefereeAssignment.match_id == match_id,
        RefereeAssignment.referee_user_id == request.referee_user_id
    ).first()
    
    if assignment:
        assignment.status = RefereeAssignmentStatus.OFFERED
    else:
        assignment = RefereeAssignment(
            match_id=match_id,
            referee_user_id=request.referee_user_id,
            status=RefereeAssignmentStatus.OFFERED
        )
        db.add(assignment)
    
    db.commit()
    db.refresh(assignment)
    
    return {"assignment_id": str(assignment.id), "status": assignment.status.value}

@router.post("/{match_id}/referee/accept")
async def accept_referee_assignment(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Referee accepts assignment"""
    if current_user.role != UserRole.REFEREE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only referees can accept assignments"
        )
    
    assignment = db.query(RefereeAssignment).filter(
        RefereeAssignment.match_id == match_id,
        RefereeAssignment.referee_user_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    assignment.status = RefereeAssignmentStatus.ACCEPTED
    assignment.responded_at = datetime.utcnow()
    
    db.commit()
    
    return {"status": "accepted", "assignment_id": str(assignment.id)}

@router.post("/{match_id}/start")
async def start_match(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a match - only referee can do this"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Check if user is assigned referee
    assignment = db.query(RefereeAssignment).filter(
        RefereeAssignment.match_id == match_id,
        RefereeAssignment.referee_user_id == current_user.id,
        RefereeAssignment.status == RefereeAssignmentStatus.ACCEPTED
    ).first()
    
    if not assignment and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned referee can start the match"
        )
    
    match.status = MatchStatus.LIVE
    match.started_at = datetime.utcnow()
    
    # Create KICKOFF event
    last_seq = db.query(func.max(MatchEvent.seq)).filter(
        MatchEvent.match_id == match_id
    ).scalar() or 0
    
    kickoff_event = MatchEvent(
        match_id=match_id,
        seq=last_seq + 1,
        ts=datetime.utcnow(),
        type="KICKOFF",
        payload_json={},
        created_by_user_id=current_user.id
    )
    
    db.add(kickoff_event)
    db.commit()
    
    return {"status": "started", "match_id": str(match.id)}

@router.post("/{match_id}/events", response_model=MatchEventResponse, status_code=status.HTTP_201_CREATED)
async def create_match_event(
    match_id: UUID,
    request: MatchEventCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a match event (append-only with seq enforcement)"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    if match.status != MatchStatus.LIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match is not live"
        )
    
    # Check if user is assigned referee
    assignment = db.query(RefereeAssignment).filter(
        RefereeAssignment.match_id == match_id,
        RefereeAssignment.referee_user_id == current_user.id,
        RefereeAssignment.status == RefereeAssignmentStatus.ACCEPTED
    ).first()
    
    if not assignment and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned referee can create events"
        )
    
    # Get last sequence number
    last_seq = db.query(func.max(MatchEvent.seq)).filter(
        MatchEvent.match_id == match_id
    ).scalar() or 0
    
    # Enforce strict ordering
    if request.seq != last_seq + 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected sequence {last_seq + 1}, got {request.seq}"
        )
    
    # Check uniqueness
    existing = db.query(MatchEvent).filter(
        MatchEvent.match_id == match_id,
        MatchEvent.seq == request.seq
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Event with this sequence already exists"
        )
    
    event = MatchEvent(
        match_id=match_id,
        seq=request.seq,
        ts=request.ts,
        type=request.type,
        payload_json=request.payload,
        created_by_user_id=current_user.id
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return event

@router.post("/{match_id}/finalize")
async def finalize_match(
    match_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finalize a match - triggers report generation"""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    if match.status != MatchStatus.LIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Match is not live"
        )
    
    # Check if user is assigned referee
    assignment = db.query(RefereeAssignment).filter(
        RefereeAssignment.match_id == match_id,
        RefereeAssignment.referee_user_id == current_user.id,
        RefereeAssignment.status == RefereeAssignmentStatus.ACCEPTED
    ).first()
    
    if not assignment and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only assigned referee can finalize the match"
        )
    
    match.status = MatchStatus.FINAL
    match.finalized_at = datetime.utcnow()
    
    # Create FINAL_WHISTLE event
    last_seq = db.query(func.max(MatchEvent.seq)).filter(
        MatchEvent.match_id == match_id
    ).scalar() or 0
    
    final_event = MatchEvent(
        match_id=match_id,
        seq=last_seq + 1,
        ts=datetime.utcnow(),
        type="FINAL_WHISTLE",
        payload_json={},
        created_by_user_id=current_user.id
    )
    
    db.add(final_event)
    
    # Enqueue report generation job
    from app.tasks.reports import generate_match_report_task
    generate_match_report_task.delay(str(match.id))
    
    db.commit()
    
    return {"status": "finalized", "match_id": str(match.id)}

@router.get("/{match_id}/events", response_model=List[MatchEventResponse])
async def get_match_events(
    match_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all events for a match"""
    events = db.query(MatchEvent).filter(
        MatchEvent.match_id == match_id
    ).order_by(MatchEvent.seq).all()
    
    return events

