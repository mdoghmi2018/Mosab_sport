from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base

class PaymentStatus(str, enum.Enum):
    INITIATED = "initiated"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(50), nullable=False)  # stripe, paypal, custom
    provider_ref = Column(String(255), nullable=True)  # External payment reference
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.INITIATED, nullable=False)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    reservation = relationship("Reservation", backref="payment")
    events = relationship("PaymentEvent", back_populates="payment")

class PaymentEvent(Base):
    __tablename__ = "payment_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=True)
    provider = Column(String(50), nullable=False)
    provider_event_id = Column(String(255), nullable=False)  # Unique event ID from provider
    payload_json = Column(JSONB, nullable=False)  # Full webhook payload
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    payment = relationship("Payment", back_populates="events")
    
    __table_args__ = (
        UniqueConstraint("provider", "provider_event_id", name="uq_payment_event_provider_id"),
        Index("idx_payment_event_provider", "provider", "provider_event_id"),
    )

