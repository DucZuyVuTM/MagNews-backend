from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..auth import get_current_user
from ..models import User
from ..schemas import ComplaintCreate, ComplaintStatusUpdate, ComplaintResponse
from ..services.complaint_service import ComplaintService

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


def get_complaint_service(db: Session = Depends(get_db)):
    return ComplaintService(db)


@router.post("/", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def submit_complaint(
    complaint: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    return service.create(complaint, current_user)


@router.get("/my", response_model=List[ComplaintResponse])
def get_my_complaints(
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    return service.list_my(current_user)


@router.get("/", response_model=List[ComplaintResponse])
def list_all_complaints(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    return service.list_all(current_user, status_filter)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    return service.get_by_id(complaint_id, current_user)


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    complaint_id: int,
    payload: ComplaintStatusUpdate,
    current_user: User = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    return service.update_status(complaint_id, payload, current_user)
