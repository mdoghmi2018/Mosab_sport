from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base

class AwardKind(str, enum.Enum):
    MAN_OF_MATCH = "man_of_match"
    BEST_GOAL = "best_goal"

class MatchAward(Base):
    __tablename__ = "match_awards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    kind = Column(SQLEnum(AwardKind), nullable=False)
    winner_ref = Column(String(255), nullable=False)  # player_id or event_id
    decided_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decided_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    match = relationship("Match", back_populates="awards")

