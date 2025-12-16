from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..auth import get_current_user
from ..models import User, PublicationType
from ..schemas import PublicationCreate, PublicationUpdate, PublicationResponse
from ..services.publication_service import PublicationService

router = APIRouter(prefix="/api/publications", tags=["publications"])

def get_publication_service(db: Session = Depends(get_db)):
    return PublicationService(db)

@router.post("/", response_model=PublicationResponse, status_code=status.HTTP_201_CREATED)
def create_publication(
    publication: PublicationCreate,
    current_user: User = Depends(get_current_user),
    service: PublicationService = Depends(get_publication_service)
):
    return service.create(publication, current_user)

@router.get("/", response_model=List[PublicationResponse])
def list_publications(
    skip: Optional[int] = None,
    limit: Optional[int] = None,
    type: Optional[PublicationType] = None,
    service: PublicationService = Depends(get_publication_service)
):
    return service.get_list(skip, limit, type)

@router.get("/all", response_model=List[PublicationResponse])
def list_all_for_admin(
    current_user: User = Depends(get_current_user),
    service: PublicationService = Depends(get_publication_service)
):
    return service.get_list_admin(current_user)

@router.get("/{publication_id}", response_model=PublicationResponse)
def get_publication(
    publication_id: int,
    current_user: User = Depends(get_current_user),
    service: PublicationService = Depends(get_publication_service)
):
    return service.get_by_id(publication_id, current_user)

@router.patch("/{publication_id}", response_model=PublicationResponse)
def update_publication(
    publication_id: int,
    publication_update: PublicationUpdate,
    current_user: User = Depends(get_current_user),
    service: PublicationService = Depends(get_publication_service)
):
    return service.update(publication_id, publication_update, current_user)

@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_publication(
    publication_id: int,
    current_user: User = Depends(get_current_user),
    service: PublicationService = Depends(get_publication_service)
):
    return service.soft_delete(publication_id, current_user)
