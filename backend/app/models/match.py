from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base

class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINAL = "final"
    ABANDONED = "abandoned"

class RefereeAssignmentStatus(str, enum.Enum):
    OFFERED = "offered"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REPLACED = "replaced"

class ReportStatus(str, enum.Enum):
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"

class Match(Base):
    __tablename__ = "matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reservation_id = Column(UUID(as_uuid=True), ForeignKey("reservations.id"), nullable=False, unique=True)
    sport = Column(String(50), nullable=False)
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.SCHEDULED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    
    reservation = relationship("Reservation", back_populates="match")
    referee_assignments = relationship("RefereeAssignment", back_populates="match", cascade="all, delete-orphan")
    events = relationship("MatchEvent", back_populates="match", cascade="all, delete-orphan", order_by="MatchEvent.seq")
    reports = relationship("MatchReport", back_populates="match", cascade="all, delete-orphan")
    awards = relationship("MatchAward", back_populates="match", cascade="all, delete-orphan")

class RefereeAssignment(Base):
    __tablename__ = "referee_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    referee_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(RefereeAssignmentStatus), default=RefereeAssignmentStatus.OFFERED, nullable=False)
    offered_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)

class MatchEvent(Base):
    __tablename__ = "match_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    seq = Column(Integer, nullable=False)  # Sequence number (1, 2, 3...)
    ts = Column(DateTime(timezone=True), nullable=False)  # Event timestamp
    type = Column(String(50), nullable=False)  # KICKOFF, GOAL, CARD, SUBSTITUTION, FINAL_WHISTLE, etc
    payload_json = Column(JSONB, nullable=False)  # Event-specific data
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    match = relationship("Match", back_populates="events")
    
    __table_args__ = (
        UniqueConstraint("match_id", "seq", name="uq_match_event_seq"),
        Index("idx_match_event_match_seq", "match_id", "seq"),
    )

class MatchReport(Base):
    __tablename__ = "match_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.GENERATING, nullable=False)
    pdf_url = Column(String(500), nullable=True)
    checksum = Column(String(64), nullable=True)  # SHA256 checksum
    report_json = Column(JSONB, nullable=True)  # Canonical report data
    generated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    match = relationship("Match", back_populates="reports")
    
    __table_args__ = (
        UniqueConstraint("match_id", "version", name="uq_match_report_version"),
        Index("idx_match_report_match_version", "match_id", "version"),
    )

