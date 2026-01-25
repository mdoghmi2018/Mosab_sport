from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base

class ActorType(str, enum.Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"
    SCHOOL = "school"
    ACADEMY = "academy"

class ReservationStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id = Column(UUID(as_uuid=True), ForeignKey("slots.id"), nullable=False)
    booked_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    actor_type = Column(SQLEnum(ActorType), nullable=False)
    actor_id = Column(String(255), nullable=True)  # Optional: company/school/academy ID
    status = Column(SQLEnum(ReservationStatus), default=ReservationStatus.PENDING, nullable=False)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For pending reservations
    
    slot = relationship("Slot", back_populates="reservation")
    match = relationship("Match", back_populates="reservation", uselist=False)
    
    # Note: Partial unique constraint for paid reservations is enforced at application level
    # Database-level partial unique constraints require PostgreSQL 9.2+ and specific syntax
    # For now, we enforce this in the application logic

