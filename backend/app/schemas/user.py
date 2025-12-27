from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)  # Correspond à la base de données

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=255)  # Correspond à la base de données

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: int
    is_active: bool
    
    class Config:
        from_attributes = True