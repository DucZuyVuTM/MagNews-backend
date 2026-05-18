from sqlalchemy import (
    Column,
    BigInteger,
    CheckConstraint,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Enum,
    Boolean,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .database import Base


def _pk():
    return Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, index=True)


def _fk(target: str, nullable: bool = False):
    return Column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey(target),
        nullable=nullable,
    )

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    PROVIDER = "provider"

class PublicationType(str, enum.Enum):
    # На витрине: журналы, газеты, научные журналы.
    # Расширяется на цифровой контент добавлением новых значений (без миграции
    # данных — в БД хранится строковое значение enum).
    MAGAZINE = "magazine"
    NEWSPAPER = "newspaper"
    JOURNAL = "journal"

class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class ComplaintStatus(str, enum.Enum):
    NEW = "new"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class ModerationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id = _pk()
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    company_name = Column(String, nullable=True)
    inn = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    subscriptions = relationship("Subscription", back_populates="user")
    complaints = relationship("Complaint", back_populates="user")
    publications = relationship("Publication", back_populates="provider")
    reviews = relationship("Review", back_populates="user")

class Publication(Base):
    __tablename__ = "publications"

    id = _pk()
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
    provider_id = _fk("users.id", nullable=True)
    moderation_status = Column(
        Enum(ModerationStatus),
        default=ModerationStatus.PENDING,
        nullable=False,
    )
    moderation_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    subscriptions = relationship("Subscription", back_populates="publication")
    complaints = relationship("Complaint", back_populates="publication")
    provider = relationship("User", back_populates="publications")
    reviews = relationship("Review", back_populates="publication")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = _pk()
    user_id = _fk("users.id")
    publication_id = _fk("publications.id")
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)
    price = Column(Float, nullable=False)
    auto_renew = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="subscriptions")
    publication = relationship("Publication", back_populates="subscriptions")


class Complaint(Base):
    __tablename__ = "complaints"

    id = _pk()
    user_id = _fk("users.id")
    publication_id = _fk("publications.id")
    reason = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(ComplaintStatus), default=ComplaintStatus.NEW, nullable=False)
    resolution_note = Column(Text)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="complaints")
    publication = relationship("Publication", back_populates="complaints")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "publication_id", name="uq_reviews_user_publication"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
    )

    id = _pk()
    user_id = _fk("users.id")
    publication_id = _fk("publications.id")
    rating = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="reviews")
    publication = relationship("Publication", back_populates="reviews")
