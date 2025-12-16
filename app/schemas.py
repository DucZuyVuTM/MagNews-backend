from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator
from datetime import datetime
from typing import Optional

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)

    @validator("password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise HTTPException(status_code=400, detail="Password must contain at least 1 uppercase letter")
        if not any(c.islower() for c in v):
            raise HTTPException(status_code=400, detail="Password must contain at least 1 lowercase letter")
        if not any(c.isdigit() for c in v):
            raise HTTPException(status_code=400, detail="Password must contain at least 1 number")
        return v

class UserLogin(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    
    model_config = ConfigDict(extra="forbid")

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Schemas for Changing Password
class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator("new_password")
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise HTTPException(status_code=400, detail="Password must contain at least 1 uppercase letter")
        if not any(c.islower() for c in v):
            raise HTTPException(status_code=400, detail="Password must contain at least 1 lowercase letter")
        if not any(c.isdigit() for c in v):
            raise HTTPException(status_code=400, detail="Password must contain at least 1 number")
        return v

    model_config = ConfigDict(populate_by_name=True)

class ChangePasswordResponse(BaseModel):
    message: str = "Password changed successfully"

# Publication Schemas
class PublicationBase(BaseModel):
    title: str
    description: Optional[str] = None
    type: str
    publisher: Optional[str] = None
    frequency: Optional[str] = None
    price_monthly: float = Field(gt=0)
    price_yearly: float = Field(gt=0)
    cover_image_url: Optional[str] = None

class PublicationCreate(PublicationBase):
    pass

class PublicationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    publisher: Optional[str] = None
    frequency: Optional[str] = None
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    cover_image_url: Optional[str] = None
    is_visible: Optional[bool] = None
    is_available: Optional[bool] = None

class PublicationResponse(PublicationBase):
    id: int
    is_visible: bool
    is_available: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Subscription Schemas
class SubscriptionCreate(BaseModel):
    publication_id: int
    duration_months: int = Field(ge=1, le=36)
    auto_renew: bool = False

class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    publication_id: int
    start_date: datetime
    end_date: datetime
    status: str
    price: float
    auto_renew: bool
    created_at: datetime
    publication: PublicationResponse

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str
