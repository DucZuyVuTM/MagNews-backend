from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..schemas import SubscriptionCreate, SubscriptionResponse
from ..services.subscription_service import SubscriptionService

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

def get_subscription_service(db: Session = Depends(get_db)):
    return SubscriptionService(db)

@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    subscription: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    return service.create(subscription, current_user)

@router.get("/my", response_model=List[SubscriptionResponse])
def get_my_subscriptions(
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    return service.get_my_subscriptions(current_user)

@router.delete("/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    service: SubscriptionService = Depends(get_subscription_service)
):
    return service.cancel(subscription_id, current_user)
