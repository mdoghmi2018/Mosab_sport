from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class PlayerProfile(Base):
    __tablename__ = "player_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True, index=True)
    photo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Squad(Base):
    __tablename__ = "squads"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_name = Column(String(255), nullable=False)
    sport = Column(String(50), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    members = relationship("SquadMember", back_populates="squad", cascade="all, delete-orphan")
    formations = relationship("Formation", back_populates="squad")

class SquadMember(Base):
    __tablename__ = "squad_members"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id"), nullable=False)
    player_profile_id = Column(UUID(as_uuid=True), ForeignKey("player_profiles.id"), nullable=False)
    jersey_no = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    squad = relationship("Squad", back_populates="members")
    player_profile = relationship("PlayerProfile")
    
    __table_args__ = (
        Index("idx_squad_member_squad", "squad_id"),
    )

class Formation(Base):
    __tablename__ = "formations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=True)
    squad_id = Column(UUID(as_uuid=True), ForeignKey("squads.id"), nullable=True)
    shape = Column(String(50), nullable=False)  # "4-4-2", "3-5-2", etc
    positions_json = Column(JSONB, nullable=False)  # {player_id: {position, x, y}, ...}
    share_token = Column(String(64), unique=True, nullable=False, index=True)
    share_permission = Column(String(20), default="view", nullable=False)  # view, edit
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    squad = relationship("Squad", back_populates="formations")
    
    __table_args__ = (
        Index("idx_formation_match", "match_id"),
        Index("idx_formation_squad", "squad_id"),
    )

