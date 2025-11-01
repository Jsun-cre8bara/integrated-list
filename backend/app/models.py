from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class RoleEnum(str, Enum):
    USER = "user"
    MERCHANT = "merchant"
    ADMIN = "admin"


class StampStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class FraudStatus(str, Enum):
    OPEN = "open"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default=RoleEnum.USER.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    stamp_books: Mapped[List["StampBook"]] = relationship("StampBook", back_populates="user")
    merchants: Mapped[List["Merchant"]] = relationship("Merchant", back_populates="owner")


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(String(120))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    owner: Mapped[User] = relationship("User", back_populates="merchants")
    stamp_books: Mapped[List["Stamp"]] = relationship("Stamp", back_populates="merchant")
    contracts: Mapped[List["MerchantContract"]] = relationship("MerchantContract", back_populates="merchant")
    qr_tokens: Mapped[List["QRToken"]] = relationship("QRToken", back_populates="merchant")


class MerchantContract(Base):
    __tablename__ = "merchant_contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fee_plan: Mapped[Optional[str]] = mapped_column(String(120))
    discount_rate: Mapped[Optional[float]] = mapped_column(Float)

    merchant: Mapped[Merchant] = relationship("Merchant", back_populates="contracts")


class Performance(Base):
    __tablename__ = "performances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    venue: Mapped[Optional[str]] = mapped_column(String(255))
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    stamp_books: Mapped[List["StampBook"]] = relationship("StampBook", back_populates="performance")


class StampBook(Base):
    __tablename__ = "stamp_books"
    __table_args__ = (
        UniqueConstraint("user_id", "performance_id", name="uq_stampbook_user_performance"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    performance_id: Mapped[int] = mapped_column(ForeignKey("performances.id"))
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")

    user: Mapped[User] = relationship("User", back_populates="stamp_books")
    performance: Mapped[Performance] = relationship("Performance", back_populates="stamp_books")
    stamps: Mapped[List["Stamp"]] = relationship("Stamp", back_populates="stamp_book")


class QRToken(Base):
    __tablename__ = "qr_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    token_hash: Mapped[str] = mapped_column(String(255), unique=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    merchant: Mapped[Merchant] = relationship("Merchant", back_populates="qr_tokens")
    stamps: Mapped[List["Stamp"]] = relationship("Stamp", back_populates="qr_token")


class Stamp(Base):
    __tablename__ = "stamps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stamp_book_id: Mapped[int] = mapped_column(ForeignKey("stamp_books.id"))
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    qr_token_id: Mapped[Optional[int]] = mapped_column(ForeignKey("qr_tokens.id"), nullable=True)
    visit_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    discount_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    approval_method: Mapped[Optional[str]] = mapped_column(String(50))
    photo_url: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default=StampStatus.PENDING.value)

    stamp_book: Mapped[StampBook] = relationship("StampBook", back_populates="stamps")
    merchant: Mapped[Merchant] = relationship("Merchant", back_populates="stamp_books")
    qr_token: Mapped[Optional[QRToken]] = relationship("QRToken", back_populates="stamps")
    transaction: Mapped[Optional["Transaction"]] = relationship(
        "Transaction", back_populates="stamp", uselist=False
    )
    fraud_alerts: Mapped[List["FraudAlert"]] = relationship("FraudAlert", back_populates="stamp")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stamp_id: Mapped[int] = mapped_column(ForeignKey("stamps.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    payment_method: Mapped[str] = mapped_column(String(50))
    receipt_reference: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    stamp: Mapped[Stamp] = relationship("Stamp", back_populates="transaction")


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50))
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    target_rules: Mapped[Optional[str]] = mapped_column(Text)

    events: Mapped[List["CampaignEvent"]] = relationship("CampaignEvent", back_populates="campaign")


class CampaignEvent(Base):
    __tablename__ = "campaign_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    merchant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("merchants.id"), nullable=True)
    stamp_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stamps.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    campaign: Mapped[Campaign] = relationship("Campaign", back_populates="events")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    actor_role: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(255))
    target_type: Mapped[str] = mapped_column(String(120))
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    stamp_id: Mapped[int] = mapped_column(ForeignKey("stamps.id"))
    reason: Mapped[str] = mapped_column(String(255))
    score: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default=FraudStatus.OPEN.value)
    resolved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    stamp: Mapped[Stamp] = relationship("Stamp", back_populates="fraud_alerts")
