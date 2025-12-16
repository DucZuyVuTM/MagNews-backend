from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException

from ..models import Subscription, Publication, User, SubscriptionStatus
from ..schemas import SubscriptionCreate, SubscriptionResponse

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: SubscriptionCreate, current_user: User) -> SubscriptionResponse:
        if not current_user.is_active:
            raise HTTPException(status_code=403, detail="User is deactivated")

        publication = self.db.query(Publication).filter(
            Publication.id == data.publication_id,
            Publication.is_available == True,
            Publication.is_visible == True
        ).first()

        if not publication:
            raise HTTPException(status_code=404, detail="Publication not found or not available")

        # Check for duplicate active subscriptions
        existing = self.db.query(Subscription).filter(
            Subscription.user_id == current_user.id,
            Subscription.publication_id == data.publication_id,
            Subscription.status == SubscriptionStatus.ACTIVE
        ).first()

        if existing:
            raise HTTPException(status_code=400, detail="Active subscription already exists")

        # Calculate price
        months = data.duration_months
        if months >= 12 and months % 12 == 0:
            price = publication.price_yearly * (months // 12)
        else:
            price = publication.price_monthly * months

        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=30 * months)

        subscription = Subscription(
            user_id=current_user.id,
            publication_id=data.publication_id,
            start_date=start_date,
            end_date=end_date,
            status=SubscriptionStatus.ACTIVE,
            price=price,
            auto_renew=data.auto_renew
        )

        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return SubscriptionResponse.model_validate(subscription)

    def get_my_subscriptions(self, current_user: User) -> List[SubscriptionResponse]:
        subscriptions = self.db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).order_by(Subscription.created_at.desc()).all()

        return [SubscriptionResponse.model_validate(sub) for sub in subscriptions]

    def cancel(self, subscription_id: int, current_user: User) -> None:
        if not current_user.is_active:
            raise HTTPException(status_code=403, detail="User is deactivated")

        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id,
            Subscription.user_id == current_user.id
        ).first()

        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Only active subscriptions can be cancelled")

        subscription.status = SubscriptionStatus.CANCELLED
        subscription.auto_renew = False
        self.db.commit()
