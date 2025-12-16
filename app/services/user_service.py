from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Callable

from ..models import User
from ..schemas import UserCreate, UserUpdate, UserResponse, ChangePassword, ChangePasswordResponse

class UserService:
    def __init__(
        self,
        db: Session,
        hash_password: Callable[[str], str],
        verify_password: Callable[[str, str], bool],
        create_access_token: Callable[[dict], str]
    ):
        self.db = db
        self.hash_password = hash_password
        self.verify_password = verify_password
        self.create_access_token = create_access_token

    def create(self, data: UserCreate) -> UserResponse:
        if self.db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")
        if self.db.query(User).filter(User.username == data.username).first():
            raise HTTPException(status_code=400, detail="Username already taken")

        db_user = User(
            email=data.email,
            username=data.username,
            full_name=data.full_name,
            hashed_password=self.hash_password(data.password)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return UserResponse.model_validate(db_user)

    def authenticate(self, login_str: str, password: str) -> str:
        user = self.db.query(User).filter(
            (User.email == login_str) | (User.username == login_str)
        ).first()

        if not user or not self.verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect username or password")

        return self.create_access_token({"sub": str(user.id)})

    def get_current(self, current_user: User) -> UserResponse:
        return UserResponse.model_validate(current_user)

    def update_profile(self, user_update: UserUpdate, current_user: User) -> UserResponse:
        update_data = user_update.model_dump(exclude_none=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No information has been submitted for update")

        if "username" in update_data:
            if self.db.query(User).filter(
                User.username == update_data["username"],
                User.id != current_user.id
            ).first():
                raise HTTPException(status_code=400, detail="Username already taken")

        for key, value in update_data.items():
            setattr(current_user, key, value)

        self.db.commit()
        self.db.refresh(current_user)
        return UserResponse.model_validate(current_user)

    def change_password(self, payload: ChangePassword, current_user: User) -> ChangePasswordResponse:
        if not self.verify_password(payload.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        current_user.hashed_password = self.hash_password(payload.new_password)
        self.db.commit()
        return ChangePasswordResponse()
