from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException

from ..models import Publication, PublicationType, User, UserRole
from ..schemas import PublicationCreate, PublicationUpdate, PublicationResponse

class PublicationService:
    def __init__(self, db: Session):
        self.db = db

    def _clean_data(self, data_dict: dict) -> dict:
        return {
            k: None if isinstance(v, str) and v.strip() == "" else v
            for k, v in data_dict.items()
        }

    def create(self, data: PublicationCreate, current_user: User) -> PublicationResponse:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        if not current_user.is_active:
            raise HTTPException(status_code=403, detail="User is deactivated")

        cleaned_data = self._clean_data(data.model_dump())
        publication = Publication(**cleaned_data)
        self.db.add(publication)
        self.db.commit()
        self.db.refresh(publication)
        return PublicationResponse.model_validate(publication)

    def get_list(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        type_filter: Optional[PublicationType] = None
    ) -> List[PublicationResponse]:
        query = self.db.query(Publication).filter(
            Publication.is_available == True,
            Publication.is_visible == True
        ).order_by(Publication.created_at.desc())

        if type_filter is not None:
            query = query.filter(Publication.type == type_filter)
        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)

        return [PublicationResponse.model_validate(pub) for pub in query.all()]

    def get_list_admin(self, current_user: User) -> List[PublicationResponse]:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")

        publications = self.db.query(Publication).filter(
            Publication.is_available == True
        ).order_by(Publication.created_at.desc()).all()

        return [PublicationResponse.model_validate(pub) for pub in publications]

    def get_by_id(self, publication_id: int, current_user: Optional[User] = None) -> PublicationResponse:
        publication = self.db.query(Publication).filter(Publication.id == publication_id).first()
        if not publication or not publication.is_available:
            raise HTTPException(status_code=404, detail="Publication not found")

        if not publication.is_visible and (not current_user or current_user.role != UserRole.ADMIN):
            raise HTTPException(status_code=404, detail="Publication not found")

        return PublicationResponse.model_validate(publication)

    def update(self, publication_id: int, data: PublicationUpdate, current_user: User) -> PublicationResponse:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        if not current_user.is_active:
            raise HTTPException(status_code=403, detail="User is deactivated")

        publication = self.db.query(Publication).filter(Publication.id == publication_id).first()
        if not publication:
            raise HTTPException(status_code=404, detail="Publication not found")

        updated_data = self._clean_data(data.model_dump(exclude_none=True))
        for key, value in updated_data.items():
            setattr(publication, key, value)

        self.db.commit()
        self.db.refresh(publication)
        return PublicationResponse.model_validate(publication)

    def soft_delete(self, publication_id: int, current_user: User) -> None:
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        if not current_user.is_active:
            raise HTTPException(status_code=403, detail="User is deactivated")

        publication = self.db.query(Publication).filter(Publication.id == publication_id).first()
        if not publication:
            raise HTTPException(status_code=404, detail="Publication not found")

        publication.is_visible = False
        publication.is_available = False
        self.db.commit()
