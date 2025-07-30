from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Schema for user creation."""
    username: str = Field(..., description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """Schema for logging in a user."""
    username: str = Field(..., description="Username")
    password: str = Field(..., min_length=6, description="Password")

# PUBLIC_INTERFACE
class UserRead(BaseModel):
    """Schema for returning user details."""
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class NoteCreate(BaseModel):
    """Schema for note creation."""
    title: str = Field(..., description="Title for the note")
    content: str = Field(..., description="Markdown content of the note")

# PUBLIC_INTERFACE
class NoteUpdate(BaseModel):
    """Schema for note update."""
    title: Optional[str]
    content: Optional[str]

# PUBLIC_INTERFACE
class NoteRead(BaseModel):
    """Schema for returning note details."""
    id: int
    user_id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
