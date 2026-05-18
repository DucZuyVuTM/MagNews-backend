from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from ..models import Complaint, ComplaintStatus, Publication, User, UserRole
from ..schemas import ComplaintCreate, ComplaintStatusUpdate, ComplaintResponse


class ComplaintService:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: ComplaintCreate, current_user: User) -> ComplaintResponse:
        if not current_user.is_active:
            raise HTTPException(status_code=403, detail="User is deactivated")

        publication = self.db.query(Publication).filter(
            Publication.id == data.publication_id
        ).first()
        if not publication:
            raise HTTPException(status_code=404, detail="Publication not found")

        complaint = Complaint(
            user_id=current_user.id,
            publication_id=data.publication_id,
            reason=data.reason,
            description=data.description,
            status=ComplaintStatus.NEW,
        )
        self.db.add(complaint)
        self.db.commit()
        self.db.refresh(complaint)
        return ComplaintResponse.model_validate(complaint)

    def list_my(self, current_user: User) -> List[ComplaintResponse]:
        items = self.db.query(Complaint).filter(
            Complaint.user_id == current_user.id
        ).order_by(Complaint.created_at.desc()).all()
        return [ComplaintResponse.model_validate(c) for c in items]

    def list_all(self, current_user: User, status_filter: Optional[str] = None) -> List[ComplaintResponse]:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        query = self.db.query(Complaint).order_by(Complaint.created_at.desc())
        if status_filter:
            try:
                status_enum = ComplaintStatus(status_filter)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid status filter")
            query = query.filter(Complaint.status == status_enum)
        return [ComplaintResponse.model_validate(c) for c in query.all()]

    def get_by_id(self, complaint_id: int, current_user: User) -> ComplaintResponse:
        complaint = self.db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        if current_user.role != UserRole.ADMIN and complaint.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        return ComplaintResponse.model_validate(complaint)

    def update_status(
        self,
        complaint_id: int,
        payload: ComplaintStatusUpdate,
        current_user: User,
    ) -> ComplaintResponse:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        try:
            new_status = ComplaintStatus(payload.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

        complaint = self.db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")

        complaint.status = new_status
        if payload.resolution_note is not None:
            complaint.resolution_note = payload.resolution_note
        complaint.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(complaint)
        return ComplaintResponse.model_validate(complaint)
