from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base

class AdvertiserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class AdCreativeStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVOKED = "revoked"

class AdPlacementSlot(str, enum.Enum):
    PRE = "pre"
    MID = "mid"
    POST = "post"
    BANNER = "banner"

class AdPlacementStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Advertiser(Base):
    __tablename__ = "advertisers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    contact_json = Column(JSONB, nullable=False)  # {email, phone, address}
    status = Column(SQLEnum(AdvertiserStatus), default=AdvertiserStatus.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class AdCreative(Base):
    __tablename__ = "ad_creatives"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    advertiser_id = Column(UUID(as_uuid=True), ForeignKey("advertisers.id"), nullable=False)
    media_url = Column(String(500), nullable=False)
    copy = Column(String(1000), nullable=True)  # Ad text/copy
    status = Column(SQLEnum(AdCreativeStatus), default=AdCreativeStatus.DRAFT, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    decided_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(String(500), nullable=True)
    
    advertiser = relationship("Advertiser")
    placements = relationship("AdPlacement", back_populates="creative")

class AdPlacement(Base):
    __tablename__ = "ad_placements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id = Column(UUID(as_uuid=True), ForeignKey("matches.id"), nullable=False)
    slot = Column(SQLEnum(AdPlacementSlot), nullable=False)
    creative_id = Column(UUID(as_uuid=True), ForeignKey("ad_creatives.id"), nullable=False)
    status = Column(SQLEnum(AdPlacementStatus), default=AdPlacementStatus.SCHEDULED, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    creative = relationship("AdCreative", back_populates="placements")
    
    __table_args__ = (
        Index("idx_ad_placement_match_slot", "match_id", "slot"),
    )

