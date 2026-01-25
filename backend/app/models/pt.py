from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base

class PTRequestScope(str, enum.Enum):
    INDIVIDUAL = "individual"
    TEAM = "team"

class PTRequestStatus(str, enum.Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    CONFIRMED = "confirmed"

class PTRequest(Base):
    __tablename__ = "pt_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scope = Column(SQLEnum(PTRequestScope), nullable=False)
    requester_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pt_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Assigned PT
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=True)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=True)
    details = Column(JSONB, nullable=False)  # {duration, goals, preferences, etc}
    status = Column(SQLEnum(PTRequestStatus), default=PTRequestStatus.OPEN, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_pt_request_pt_status", "pt_user_id", "status"),
        Index("idx_pt_request_requester", "requester_user_id"),
    )

