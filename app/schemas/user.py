"""Pydantic v2 schemas for the User/Account entity and auth flows."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import UserRole


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, value: str) -> str:
        if not any(c.isupper() for c in value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.islower() for c in value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one digit.")
        if not any(not c.isalnum() for c in value):
            raise ValueError("Password must contain at least one special character.")
        return value


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    userId: uuid.UUID
    isMfaEnabled: bool
    isActive: bool
    createdAt: datetime
    updatedAt: datetime


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    mfaCode: str | None = Field(default=None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    expiresInMinutes: int


class MfaEnrollResponse(BaseModel):
    mfaSecret: str
    provisioningUri: str


class MfaVerifyRequest(BaseModel):
    mfaCode: str = Field(min_length=6, max_length=6)
