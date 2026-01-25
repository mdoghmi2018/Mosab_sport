from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.venue import Venue, Court, Slot, SlotStatus
from app.models.booking import Reservation, ReservationStatus, ActorType
from app.core.config import settings

router = APIRouter()

class VenueResponse(BaseModel):
    id: str
    name: str
    location_json: dict
    owner_user_id: str
    
    class Config:
        from_attributes = True

class CourtResponse(BaseModel):
    id: str
    venue_id: str
    name: str
    sport: str
    attributes_json: dict
    
    class Config:
        from_attributes = True

class SlotResponse(BaseModel):
    id: str
    court_id: str
    start_ts: datetime
    end_ts: datetime
    price_cents: int
    currency: str
    status: str
    
    class Config:
        from_attributes = True

class ReservationCreateRequest(BaseModel):
    slot_id: UUID
    actor_type: ActorType
    actor_id: Optional[str] = None

class ReservationResponse(BaseModel):
    id: str
    slot_id: str
    booked_by_user_id: str
    actor_type: str
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[VenueResponse])
async def list_venues(
    sport: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List venues with optional filters"""
    query = db.query(Venue)
    
    if sport:
        # Filter by courts with matching sport
        query = query.join(Court).filter(Court.sport == sport)
    
    if location:
        # Simple location filter (can be enhanced with geospatial queries)
        query = query.filter(Venue.location_json["address"].astext.ilike(f"%{location}%"))
    
    venues = query.distinct().all()
    return venues

@router.get("/{venue_id}/courts", response_model=List[CourtResponse])
async def list_courts(
    venue_id: UUID,
    sport: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List courts for a venue"""
    query = db.query(Court).filter(Court.venue_id == venue_id)
    
    if sport:
        query = query.filter(Court.sport == sport)
    
    courts = query.all()
    return courts

@router.get("/courts/{court_id}/slots", response_model=List[SlotResponse])
async def list_slots(
    court_id: UUID,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """List available slots for a court"""
    query = db.query(Slot).filter(Slot.court_id == court_id)
    
    if from_date:
        query = query.filter(Slot.start_ts >= from_date)
    if to_date:
        query = query.filter(Slot.end_ts <= to_date)
    
    # Only show open or held slots (held will expire if not paid)
    query = query.filter(Slot.status.in_([SlotStatus.OPEN, SlotStatus.HELD]))
    
    slots = query.order_by(Slot.start_ts).all()
    return slots

@router.post("/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    request: ReservationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a reservation with hold TTL"""
    # Get slot and verify it's available
    slot = db.query(Slot).filter(Slot.id == request.slot_id).first()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found"
        )
    
    # Check if there's already a paid reservation for this slot
    existing_paid = db.query(Reservation).filter(
        Reservation.slot_id == request.slot_id,
        Reservation.status == ReservationStatus.PAID
    ).first()
    
    if existing_paid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot is already booked"
        )
    
    # Use SELECT FOR UPDATE to prevent race conditions
    from sqlalchemy import select
    from sqlalchemy.orm import with_for_update
    
    # Lock the slot row for update to prevent concurrent modifications
    slot = db.query(Slot).with_for_update().filter(Slot.id == request.slot_id).first()
    
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found"
        )
    
    # Re-check paid reservation after lock
    existing_paid = db.query(Reservation).filter(
        Reservation.slot_id == request.slot_id,
        Reservation.status == ReservationStatus.PAID
    ).first()
    
    if existing_paid:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot is already booked"
        )
    
    # Transaction: check and update slot status
    if slot.status != SlotStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot is not available"
        )
    
    # Set slot to HELD and create reservation
    slot.status = SlotStatus.HELD
    expires_at = datetime.utcnow() + timedelta(minutes=settings.HOLD_TTL_MINUTES)
    
    reservation = Reservation(
        slot_id=request.slot_id,
        booked_by_user_id=current_user.id,
        actor_type=request.actor_type,
        actor_id=request.actor_id,
        status=ReservationStatus.PENDING,
        expires_at=expires_at
    )
    
    db.add(reservation)
    db.commit()
    db.refresh(reservation)
    
    return reservation

@router.get("/reservations/my", response_model=List[ReservationResponse])
async def my_reservations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's reservations"""
    reservations = db.query(Reservation).filter(
        Reservation.booked_by_user_id == current_user.id
    ).order_by(Reservation.created_at.desc()).all()
    
    return reservations

