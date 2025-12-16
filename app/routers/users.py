from fastapi import APIRouter, Depends, Form, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserUpdate, UserResponse, ChangePassword, ChangePasswordResponse, Token
from ..auth import get_current_user, get_password_hash, verify_password, create_access_token
from ..services.user_service import UserService

router = APIRouter(prefix="/api/users", tags=["users"])

def get_user_service(db: Session = Depends(get_db)):
    return UserService(
        db=db,
        hash_password=get_password_hash,
        verify_password=verify_password,
        create_access_token=create_access_token
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    return service.create(user)

@router.post("/login", response_model=Token)
def login(
    login: str = Form(..., description="Email or username"),
    password: str = Form(...),
    service: UserService = Depends(get_user_service)
):
    access_token = service.authenticate(login, password)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return service.get_current(current_user)

@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return service.update_profile(user_update, current_user)

@router.post("/me/password", response_model=ChangePasswordResponse)
def change_password(
    payload: ChangePassword,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    return service.change_password(payload, current_user)
