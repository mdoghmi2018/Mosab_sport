from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from uuid import UUID
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole
from app.models.event import Event, EventType, EventStatus, MatchFormat
from app.models.booking import Reservation, RecurrencePattern
from app.models.match import Match
from app.models.addon import Addon, AddonStatus
from app.models.formation import Formation
from app.models.venue import Slot, SlotStatus

router = APIRouter()

# Request/Response Models
class OrganizeEventRequest(BaseModel):
    # Step 1: Sport Selection
    sport: str
    
    # Step 2: Match Format
    match_format: MatchFormat
    players_per_team: int
    total_players: int
    
    # Step 3: Event Type
    event_type: EventType
    
    # Step 4: Event Details
    event_date: datetime
    event_time: Optional[str] = None  # "HH:MM" format
    is_recurring: bool = False
    recurrence_pattern: Optional[RecurrencePattern] = None
    recurrence_end_date: Optional[datetime] = None
    
    # Court/Venue Selection
    use_own_court: bool = False
    slot_id: Optional[UUID] = None  # If using venue court
    custom_venue_json: Optional[Dict[str, Any]] = None  # If using own court
    
    # Step 5: Player Import
    players_json: Optional[List[Dict[str, Any]]] = None  # List of {name, jersey_number}
    
    # Step 6: Formation
    formation_id: Optional[UUID] = None
    
    # Step 7: Add-ons
    selected_addons_json: Optional[List[str]] = None  # Array of addon IDs
    
    # Step 8: Review & Submit
    submit_for_approval: bool = False  # If True, submit immediately

class EventResponse(BaseModel):
    id: str
    organizer_user_id: str
    sport: str
    match_format: str
    players_per_team: int
    total_players: int
    event_type: str
    event_date: datetime
    event_time: Optional[str]
    is_recurring: bool
    recurrence_pattern: Optional[str]
    recurrence_end_date: Optional[datetime]
    use_own_court: bool
    slot_id: Optional[str]
    custom_venue_json: Optional[Dict[str, Any]]
    players_json: Optional[List[Dict[str, Any]]]
    formation_id: Optional[str]
    selected_addons_json: Optional[List[str]]
    status: str
    total_cost_cents: Optional[int]
    currency: str
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

def calculate_players_from_format(match_format: MatchFormat) -> Tuple[int, int]:
    """Calculate players_per_team and total_players from match format"""
    format_map = {
        MatchFormat.FIVE_X_FIVE: (5, 10),
        MatchFormat.SIX_X_SIX: (6, 12),
        MatchFormat.SEVEN_X_SEVEN: (7, 14),
        MatchFormat.EIGHT_X_EIGHT: (8, 16),
        MatchFormat.NINE_X_NINE: (9, 18),
        MatchFormat.TEN_X_TEN: (10, 20),
        MatchFormat.ELEVEN_X_ELEVEN: (11, 22),
    }
    return format_map.get(match_format, (8, 16))

def calculate_total_cost(
    slot_price_cents: Optional[int],
    addon_ids: Optional[List[str]],
    db: Session
) -> int:
    """Calculate total cost (slot + add-ons)"""
    total = slot_price_cents or 0
    
    if addon_ids:
        addons = db.query(Addon).filter(
            Addon.id.in_([UUID(aid) for aid in addon_ids]),
            Addon.status == AddonStatus.ACTIVE
        ).all()
        total += sum(addon.price_cents for addon in addons)
    
    return total

@router.post("/organize", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def organize_event(
    request: OrganizeEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new event (8-step workflow)"""
    
    # Validate match format and calculate players
    calculated_players_per_team, calculated_total = calculate_players_from_format(request.match_format)
    if request.players_per_team != calculated_players_per_team:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"players_per_team must be {calculated_players_per_team} for format {request.match_format.value}"
        )
    if request.total_players != calculated_total:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"total_players must be {calculated_total} for format {request.match_format.value}"
        )
    
    # Validate court selection
    if not request.use_own_court and not request.slot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either use_own_court must be True or slot_id must be provided"
        )
    
    if request.use_own_court and not request.custom_venue_json:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="custom_venue_json is required when use_own_court is True"
        )
    
    if not request.use_own_court and request.slot_id:
        # Verify slot exists and is available
        slot = db.query(Slot).filter(Slot.id == request.slot_id).first()
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot not found"
            )
        if slot.status != SlotStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Slot is not available"
            )
        slot_price_cents = slot.price_cents
    else:
        slot_price_cents = None
    
    # Validate recurring pattern
    if request.is_recurring and not request.recurrence_pattern:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="recurrence_pattern is required when is_recurring is True"
        )
    
    if request.is_recurring and not request.recurrence_end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="recurrence_end_date is required when is_recurring is True"
        )
    
    # Validate formation if provided
    if request.formation_id:
        formation = db.query(Formation).filter(Formation.id == request.formation_id).first()
        if not formation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Formation not found"
            )
    
    # Validate add-ons if provided
    if request.selected_addons_json:
        addon_ids = [UUID(aid) for aid in request.selected_addons_json]
        addons = db.query(Addon).filter(
            Addon.id.in_(addon_ids),
            Addon.status == AddonStatus.ACTIVE
        ).all()
        if len(addons) != len(addon_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more add-ons not found or inactive"
            )
    
    # Calculate total cost
    total_cost_cents = calculate_total_cost(
        slot_price_cents,
        request.selected_addons_json,
        db
    )
    
    # Create event
    event = Event(
        organizer_user_id=current_user.id,
        sport=request.sport,
        match_format=request.match_format,
        players_per_team=request.players_per_team,
        total_players=request.total_players,
        event_type=request.event_type,
        event_date=request.event_date,
        event_time=request.event_time,
        is_recurring=request.is_recurring,
        recurrence_pattern=request.recurrence_pattern,
        recurrence_end_date=request.recurrence_end_date,
        use_own_court=request.use_own_court,
        slot_id=request.slot_id,
        custom_venue_json=request.custom_venue_json,
        players_json=request.players_json,
        formation_id=request.formation_id,
        selected_addons_json=request.selected_addons_json,
        status=EventStatus.PENDING_APPROVAL if request.submit_for_approval else EventStatus.DRAFT,
        total_cost_cents=total_cost_cents,
        currency="USD",
        submitted_at=datetime.utcnow() if request.submit_for_approval else None
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return event

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get event details"""
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Only organizer or admin can view
    if event.organizer_user_id != current_user.id and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this event"
        )
    
    return event

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update event (only if draft)"""
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.organizer_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this event"
        )
    
    if event.status != EventStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update events in draft status"
        )
    
    # Update allowed fields
    allowed_fields = {
        "sport", "match_format", "players_per_team", "total_players",
        "event_type", "event_date", "event_time", "is_recurring",
        "recurrence_pattern", "recurrence_end_date", "use_own_court",
        "slot_id", "custom_venue_json", "players_json", "formation_id",
        "selected_addons_json"
    }
    
    for key, value in request.items():
        if key in allowed_fields:
            setattr(event, key, value)
    
    # Recalculate total cost if slot or add-ons changed
    if "slot_id" in request or "selected_addons_json" in request:
        slot_price_cents = None
        if event.slot_id:
            slot = db.query(Slot).filter(Slot.id == event.slot_id).first()
            if slot:
                slot_price_cents = slot.price_cents
        
        event.total_cost_cents = calculate_total_cost(
            slot_price_cents,
            event.selected_addons_json,
            db
        )
    
    db.commit()
    db.refresh(event)
    
    return event

@router.post("/{event_id}/submit", response_model=EventResponse)
async def submit_event_for_approval(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit event for approval"""
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.organizer_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this event"
        )
    
    if event.status != EventStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not in draft status"
        )
    
    event.status = EventStatus.PENDING_APPROVAL
    event.submitted_at = datetime.utcnow()
    
    db.commit()
    db.refresh(event)
    
    return event

@router.post("/{event_id}/approve", response_model=EventResponse)
async def approve_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve event (admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve events"
        )
    
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.status != EventStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not pending approval"
        )
    
    event.status = EventStatus.APPROVED
    event.approved_at = datetime.utcnow()
    event.approved_by_user_id = current_user.id
    
    # Create reservation when event is approved
    from app.models.booking import Reservation, ReservationStatus, ActorType
    from datetime import timedelta
    from app.core.config import settings
    
    # Check if reservation already exists
    if not event.reservation_id:
        # Create reservation based on event
        expires_at = datetime.utcnow() + timedelta(minutes=settings.HOLD_TTL_MINUTES)
        
        reservation = Reservation(
            slot_id=event.slot_id,  # May be None for own court
            booked_by_user_id=event.organizer_user_id,
            actor_type=ActorType.INDIVIDUAL,  # Default, can be enhanced
            status=ReservationStatus.PENDING,
            expires_at=expires_at,
            use_own_court=event.use_own_court,
            custom_venue_json=event.custom_venue_json,
            is_recurring=event.is_recurring,
            recurrence_pattern=event.recurrence_pattern,
            recurrence_end_date=event.recurrence_end_date
        )
        
        # If using slot, verify it's still available and lock it
        if event.slot_id:
            slot = db.query(Slot).with_for_update().filter(Slot.id == event.slot_id).first()
            if not slot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Slot not found"
                )
            
            # Check for existing paid reservation (double booking prevention)
            existing_paid = db.query(Reservation).filter(
                Reservation.slot_id == event.slot_id,
                Reservation.status == ReservationStatus.PAID
            ).first()
            
            if existing_paid:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Slot is already booked"
                )
            
            if slot.status == SlotStatus.OPEN:
                slot.status = SlotStatus.HELD
            elif slot.status != SlotStatus.HELD:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Slot is no longer available"
                )
        
        db.add(reservation)
        db.flush()  # Get reservation ID
        
        # Link event to reservation
        event.reservation_id = reservation.id
    
    db.commit()
    db.refresh(event)
    
    return event

class RejectEventRequest(BaseModel):
    rejection_reason: str

@router.post("/{event_id}/reject", response_model=EventResponse)
async def reject_event(
    event_id: UUID,
    request: RejectEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject event (admin only)"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reject events"
        )
    
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    if event.status != EventStatus.PENDING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is not pending approval"
        )
    
    event.status = EventStatus.REJECTED
    event.rejection_reason = request.rejection_reason
    
    db.commit()
    db.refresh(event)
    
    return event

