from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..schemas import (
    PublicationRatingSummary,
    ReviewCreate,
    ReviewResponse,
)
from ..services.review_service import ReviewService

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


def get_review_service(db: Session = Depends(get_db)):
    return ReviewService(db)


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_user),
    service: ReviewService = Depends(get_review_service),
):
    return service.create(review, current_user)


@router.get("/publication/{publication_id}", response_model=List[ReviewResponse])
def list_reviews(
    publication_id: int,
    service: ReviewService = Depends(get_review_service),
):
    return service.list_by_publication(publication_id)


@router.get(
    "/publication/{publication_id}/summary",
    response_model=PublicationRatingSummary,
)
def get_summary(
    publication_id: int,
    service: ReviewService = Depends(get_review_service),
):
    return service.get_summary(publication_id)
