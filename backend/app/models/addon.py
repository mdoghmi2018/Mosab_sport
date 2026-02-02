from sqlalchemy import Column, String, Integer, Boolean, DateTime, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
import enum
from app.core.database import Base

class AddonCategory(str, enum.Enum):
    OFFICIAL = "official"  # Referee
    MEDIA = "media"  # Commentator, Media Coverage, Recording, Streaming
    CEREMONY = "ceremony"  # Ceremony Stage, Fireworks, Medals & Trophies
    EQUIPMENT = "equipment"  # Jerseys & Kits
    CUSTOM = "custom"

class AddonStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"

class Addon(Base):
    __tablename__ = "addons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    category = Column(SQLEnum(AddonCategory), nullable=False)
    
    # Pricing
    price_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    # Availability
    status = Column(SQLEnum(AddonStatus), default=AddonStatus.ACTIVE, nullable=False)
    is_custom = Column(Boolean, default=False, nullable=False)  # For custom add-ons
    
    # Metadata
    metadata_json = Column(JSONB, nullable=True)  # Additional info (e.g., duration, requirements)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint("name", name="uq_addon_name"),
        Index("idx_addon_category", "category"),
        Index("idx_addon_status", "status"),
    )

