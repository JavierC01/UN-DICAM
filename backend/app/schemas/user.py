from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1, max_length=128)
