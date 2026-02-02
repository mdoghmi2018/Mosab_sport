from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from typing import TYPE_CHECKING
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.match import MatchFormat
    from app.models.booking import RecurrencePattern

# Import enums (not models) to avoid circular imports
from app.models.match import MatchFormat
from app.models.booking import RecurrencePattern

class EventType(str, enum.Enum):
    SINGLE_MATCH = "single_match"
    FRIENDLY_MATCH = "friendly_match"
    TOURNAMENT = "tournament"
    TRAINING_SESSION = "training_session"

class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class Event(Base):
    __tablename__ = "events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organizer_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Step 1: Sport Selection
    sport = Column(String(50), nullable=False)  # football, basketball, etc.
    
    # Step 2: Match Format
    match_format = Column(SQLEnum(MatchFormat), nullable=False)
    players_per_team = Column(Integer, nullable=False)  # Calculated from format
    total_players = Column(Integer, nullable=False)  # players_per_team * 2
    
    # Step 3: Event Type
    event_type = Column(SQLEnum(EventType), nullable=False)
    
    # Step 4: Event Details
    event_date = Column(DateTime(timezone=True), nullable=False)
    event_time = Column(String(10), nullable=True)  # "HH:MM" format
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_pattern = Column(SQLEnum(RecurrencePattern), nullable=True)
    recurrence_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Court/Venue Selection
    use_own_court = Column(Boolean, default=False, nullable=False)
    slot_id = Column(UUID(as_uuid=True), ForeignKey("slots.id"), nullable=True)  # If using venue court
    custom_venue_json = Column(JSONB, nullable=True)  # If using own court
    
    # Step 5: Player Import (stored as JSON)
    players_json = Column(JSONB, nullable=True)  # List of player names/numbers
    
    # Step 6: Formation
    formation_id = Column(UUID(as_uuid=True), ForeignKey("formations.id"), nullable=True)
    
    # Step 7: Add-ons (stored as JSON array of addon IDs)
    selected_addons_json = Column(JSONB, nullable=True)  # Array of addon IDs
    
    # Step 8: Review & Submit
    status = Column(SQLEnum(EventStatus), default=EventStatus.DRAFT, nullable=False)
    total_cost_cents = Column(Integer, nullable=True)  # Court booking + add-ons
    currency = Column(String(3), default="USD", nullable=False)
    
    # Approval workflow
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    
    # Relationships
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=True)  # Created after approval
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=True)  # Created after payment
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Note: Relationships are defined as foreign keys only
    # Actual relationship() definitions would require importing models, causing circular imports
    # Access related objects via direct queries when needed
    
    __table_args__ = (
        Index("idx_event_organizer", "organizer_user_id"),
        Index("idx_event_status", "status"),
        Index("idx_event_date", "event_date"),
    )

