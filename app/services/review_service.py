from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import ModerationStatus, Publication, Review, User, UserRole
from ..schemas import (
    PublicationRatingSummary,
    ReviewCreate,
    ReviewResponse,
)


class ReviewService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ReviewCreate, current_user: User) -> ReviewResponse:
        if not current_user.is_active:
            raise HTTPException(status_code=403, detail="User is deactivated")
        if current_user.role not in (UserRole.USER, UserRole.ADMIN, UserRole.PROVIDER):
            raise HTTPException(status_code=403, detail="Not enough permissions")

        publication = self.db.query(Publication).filter(
            Publication.id == data.publication_id,
            Publication.is_available == True,
            Publication.moderation_status == ModerationStatus.APPROVED,
        ).first()
        if not publication:
            raise HTTPException(status_code=404, detail="Publication not found")

        review = Review(
            user_id=current_user.id,
            publication_id=data.publication_id,
            rating=data.rating,
            text=data.text,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(review)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Review for this publication already exists",
            )
        self.db.refresh(review)
        return ReviewResponse.model_validate(review)

    def list_by_publication(self, publication_id: int) -> List[ReviewResponse]:
        reviews = self.db.query(Review).filter(
            Review.publication_id == publication_id
        ).order_by(Review.created_at.desc()).all()
        return [ReviewResponse.model_validate(r) for r in reviews]

    def get_summary(self, publication_id: int) -> PublicationRatingSummary:
        result = self.db.query(
            func.avg(Review.rating),
            func.count(Review.id),
        ).filter(Review.publication_id == publication_id).one()
        avg, count = result
        return PublicationRatingSummary(
            publication_id=publication_id,
            average_rating=float(avg) if avg is not None else None,
            review_count=int(count or 0),
        )
