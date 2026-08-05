from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str = "Consumer"
    phone: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    avatarImage: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    bio: Optional[str] = None
    avatarImage: Optional[str] = None

class UserInDB(UserBase):
    id: str = Field(alias="_id")
    passwordHash: str
    createdAt: datetime
    updatedAt: datetime

class UserOut(UserBase):
    id: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    token: Optional[str] = None
    user: UserOut
