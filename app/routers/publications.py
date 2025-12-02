from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Publication, PublicationType, User, UserRole
from ..schemas import PublicationCreate, PublicationResponse, PublicationUpdate
from ..auth import get_current_user

router = APIRouter(prefix="/api/publications", tags=["publications"])

@router.post("/", response_model=PublicationResponse, status_code=status.HTTP_201_CREATED)
def create_publication(
    publication: PublicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User is deactivated")

    created_data = publication.model_dump()

    for key, value in created_data.items():
        if isinstance(value, str) and value.strip() == "":
            created_data[key] = None

    db_publication = Publication(**created_data)
    db.add(db_publication)
    db.commit()
    db.refresh(db_publication)
    return db_publication

@router.get("/", response_model=List[PublicationResponse])
def list_publications(
    skip: Optional[int] = None,
    limit: Optional[int] = None,
    type: Optional[PublicationType] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Publication).filter(
        Publication.is_available == True,
        Publication.is_visible == True
    ).order_by(Publication.created_at.desc())
    
    if type is not None:
        query = query.filter(Publication.type == type)
    if skip is not None:
        query = query.offset(skip)
    if limit is not None:
        query = query.limit(limit)

    return query

@router.get("/all", response_model=List[PublicationResponse])
def list_all_for_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    publications = db.query(Publication).filter(
        Publication.is_available == True
    ).order_by(Publication.created_at.desc())

    return publications

@router.get("/{publication_id}", response_model=PublicationResponse)
def get_publication(
    publication_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    publication = db.query(Publication).filter(Publication.id == publication_id).first()

    if not publication or not publication.is_available:
        raise HTTPException(status_code=404, detail="Publication not found")

    if not publication.is_visible:
        if not current_user or current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=404, detail="Publication not found")

    return publication

@router.patch("/{publication_id}", response_model=PublicationResponse)
def update_publication(
    publication_id: int,
    publication_update: PublicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User is deactivated")

    db_publication = db.query(Publication).filter(Publication.id == publication_id).first()
    if not db_publication:
        raise HTTPException(status_code=404, detail="Publication not found")

    update_data = publication_update.model_dump(exclude_none=True)

    for key, value in update_data.items():
        if isinstance(value, str) and value.strip() == "":
            update_data[key] = None

    for key, value in update_data.items():
        setattr(db_publication, key, value)

    db.commit()
    db.refresh(db_publication)
    return db_publication

@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_publication(
    publication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="User is deactivated")

    db_publication = db.query(Publication).filter(Publication.id == publication_id).first()
    if not db_publication:
        raise HTTPException(status_code=404, detail="Publication not found")

    db_publication.is_visible = False
    db_publication.is_available = False
    db.commit()
