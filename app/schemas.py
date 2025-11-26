from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

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
    price_monthly: Optional[float] = None
    price_yearly: Optional[float] = None
    is_visible: Optional[bool] = None
    is_available: Optional[bool] = None

class PublicationResponse(PublicationBase):
    id: int
    is_visible: bool
    is_available: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

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
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
