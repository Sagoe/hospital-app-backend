"""Schema for front-desk patient intake — combines account creation
(email/password) with the clinical PatientProfile fields, so a
receptionist can create both in one step."""

from pydantic import EmailStr, Field, field_validator

from app.schemas.patient import PatientProfileBase


class PatientIntakeCreate(PatientProfileBase):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    nationalId: str = Field(min_length=1, max_length=64)

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