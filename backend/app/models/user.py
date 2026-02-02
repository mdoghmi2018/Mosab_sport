from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    ORGANIZER = "organizer"
    REFEREE = "referee"
    VENUE_OWNER = "venue_owner"
    PERSONAL_TRAINER = "personal_trainer"
    COMMENTATOR = "commentator"
    SUPER_ADMIN = "super_admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.ORGANIZER, nullable=False)
    verified_phone = Column(Boolean, default=False, nullable=False)
    verified_email = Column(Boolean, default=False, nullable=False)
    
    # User stats (can be calculated or stored)
    events_count = Column(Integer, default=0, nullable=False)
    wins_count = Column(Integer, default=0, nullable=False)
    rating = Column(Integer, default=0, nullable=False)  # ELO-style rating
    friends_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

