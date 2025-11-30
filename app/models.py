from sqlalchemy import Column, BigInteger, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class PublicationType(str, enum.Enum):
    MAGAZINE = "magazine"
    NEWSPAPER = "newspaper"
    JOURNAL = "journal"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    subscriptions = relationship("Subscription", back_populates="user")

class Publication(Base):
    __tablename__ = "publications"

    id = Column(BigInteger, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    type = Column(Enum(PublicationType), nullable=False)
    publisher = Column(String)
    frequency = Column(String)  # daily, weekly, monthly
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float, nullable=False)
    cover_image_url = Column(String)
    is_visible = Column(Boolean, default=True, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    subscriptions = relationship("Subscription", back_populates="publication")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    publication_id = Column(BigInteger, ForeignKey("publications.id"), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    price = Column(Float, nullable=False)
    auto_renew = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="subscriptions")
    publication = relationship("Publication", back_populates="subscriptions")
