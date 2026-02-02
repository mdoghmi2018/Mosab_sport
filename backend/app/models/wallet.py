from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    REFUND = "refund"
    EARNED = "earned"  # From matches, events, etc.

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentMethodType(str, enum.Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_ACCOUNT = "bank_account"
    DIGITAL_WALLET = "digital_wallet"

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    balance_cents = Column(Integer, default=0, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    transactions = relationship("Transaction", back_populates="wallet", cascade="all, delete-orphan")
    payment_methods = relationship("PaymentMethod", back_populates="wallet", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_wallet_user", "user_id"),
    )

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    
    amount_cents = Column(Integer, nullable=False)  # Positive for deposit/earned, negative for withdrawal/payment
    currency = Column(String(3), default="USD", nullable=False)
    
    description = Column(String(500), nullable=True)
    reference_id = Column(String(255), nullable=True)  # Reference to payment, match, etc.
    reference_type = Column(String(50), nullable=True)  # "payment", "match", "refund", etc.
    
    metadata_json = Column(JSONB, nullable=True)  # Additional transaction data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    wallet = relationship("Wallet", back_populates="transactions")
    
    __table_args__ = (
        Index("idx_transaction_wallet", "wallet_id"),
        Index("idx_transaction_type", "type"),
        Index("idx_transaction_status", "status"),
        Index("idx_transaction_created", "created_at"),
    )

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    type = Column(SQLEnum(PaymentMethodType), nullable=False)
    
    # Masked card/account info
    last_four = Column(String(4), nullable=True)  # Last 4 digits
    brand = Column(String(50), nullable=True)  # Visa, Mastercard, etc.
    
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Provider reference (e.g., Stripe payment method ID)
    provider_ref = Column(String(255), nullable=True)
    
    metadata_json = Column(JSONB, nullable=True)  # Additional payment method data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    wallet = relationship("Wallet", back_populates="payment_methods")
    
    __table_args__ = (
        Index("idx_payment_method_wallet", "wallet_id"),
        Index("idx_payment_method_default", "wallet_id", "is_default"),
    )

