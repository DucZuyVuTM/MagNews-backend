from fastapi import APIRouter, Depends, Form, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserUpdate, UserResponse, ChangePassword, ChangePasswordResponse, Token
from ..auth import pwd_context, get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    db_user = User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login", response_model=Token)
def login(
    login: str = Form(..., description="Email or username"),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        (User.email == login) | (User.username == login)
    ).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):    
    update_data = user_update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No information has been submitted for update"
        )

    if "username" in update_data:
        if db.query(User).filter(
            User.username == update_data["username"],
            User.id != current_user.id
        ).first():
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )

    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/password", response_model=ChangePasswordResponse)
def change_password(
    payload: ChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not pwd_context.verify(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    hashed_new_password = pwd_context.hash(payload.new_password)

    current_user.hashed_password = hashed_new_password
    db.commit()

    return ChangePasswordResponse()
