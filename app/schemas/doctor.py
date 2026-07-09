"""Pydantic schemas for the Doctor / Medical Staff entity."""

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AvailabilityStatus


class DoctorProfileBase(BaseModel):
    specialty: str = Field(min_length=1, max_length=150)
    licenseNumber: str = Field(min_length=1, max_length=100)
    departmentId: uuid.UUID | None = None
    consultationFee: Decimal = Field(default=Decimal("0.00"), ge=0)


class DoctorProfileCreate(DoctorProfileBase):
    userId: uuid.UUID


class DoctorProfileUpdate(BaseModel):
    specialty: str | None = Field(default=None, max_length=150)
    departmentId: uuid.UUID | None = None
    consultationFee: Decimal | None = Field(default=None, ge=0)
    availabilityStatus: AvailabilityStatus | None = None


class DoctorProfileRead(DoctorProfileBase):
    model_config = ConfigDict(from_attributes=True)

    doctorId: uuid.UUID
    userId: uuid.UUID
    availabilityStatus: AvailabilityStatus