from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone
from ..database import get_db
from ..models import Subscription, Publication, User, SubscriptionStatus
from ..schemas import SubscriptionCreate, SubscriptionResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User is deactivated")

    publication = db.query(Publication).filter(
        Publication.id == subscription.publication_id,
        Publication.is_available == True
    ).first()

    if not publication:
        raise HTTPException(status_code=404, detail="Publication not found or not available")

    # Check for existing active subscription
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.publication_id == subscription.publication_id,
        Subscription.status == SubscriptionStatus.ACTIVE
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Active subscription already exists")

    # Calculate price
    if subscription.duration_months >= 12:
        price = publication.price_yearly * (subscription.duration_months / 12)
    else:
        price = publication.price_monthly * subscription.duration_months

    start_date = datetime.now(timezone.utc)
    end_date = start_date + timedelta(days=30 * subscription.duration_months)

    db_subscription = Subscription(
        user_id=current_user.id,
        publication_id=subscription.publication_id,
        start_date=start_date,
        end_date=end_date,
        price=price,
        auto_renew=subscription.auto_renew
    )

    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription

@router.get("/my", response_model=List[SubscriptionResponse])
def get_my_subscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).order_by(Subscription.created_at.desc())

    return subscriptions

@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_subscription(
    subscription_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User is deactivated")

    subscription = db.query(Subscription).filter(
        Subscription.id == subscription_id,
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    subscription.status = SubscriptionStatus.CANCELLED
    subscription.auto_renew = False
    db.commit()
