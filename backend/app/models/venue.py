from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base

class SlotStatus(str, enum.Enum):
    OPEN = "open"
    HELD = "held"
    BOOKED = "booked"

class Venue(Base):
    __tablename__ = "venues"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    location_json = Column(JSONB, nullable=False)  # {address, city, coordinates: {lat, lng}}
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policies_json = Column(JSONB, default={})  # {cancellation_policy, refund_policy, etc}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    courts = relationship("Court", back_populates="venue", cascade="all, delete-orphan")

class Court(Base):
    __tablename__ = "courts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id = Column(UUID(as_uuid=True), ForeignKey("venues.id"), nullable=False)
    name = Column(String(255), nullable=False)
    sport = Column(String(50), nullable=False)  # football, padel, pickleball, esports
    attributes_json = Column(JSONB, default={})  # {surface, size, amenities, etc}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    venue = relationship("Venue", back_populates="courts")
    slots = relationship("Slot", back_populates="court", cascade="all, delete-orphan")

class Slot(Base):
    __tablename__ = "slots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    court_id = Column(UUID(as_uuid=True), ForeignKey("courts.id"), nullable=False)
    start_ts = Column(DateTime(timezone=True), nullable=False)
    end_ts = Column(DateTime(timezone=True), nullable=False)
    price_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(SQLEnum(SlotStatus), default=SlotStatus.OPEN, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    court = relationship("Court", back_populates="slots")
    reservation = relationship("Reservation", back_populates="slot", uselist=False, foreign_keys="Reservation.slot_id")
    
    __table_args__ = (
        UniqueConstraint("court_id", "start_ts", "end_ts", name="uq_slot_court_time"),
        Index("idx_slot_court_status", "court_id", "status"),
        Index("idx_slot_time_range", "start_ts", "end_ts"),
    )

