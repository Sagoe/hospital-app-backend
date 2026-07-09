"""Pydantic schemas for the Appointment entity."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import AppointmentStatus, AppointmentType


class AppointmentBase(BaseModel):
    startTime: datetime
    endTime: datetime
    appointmentType: AppointmentType
    reasonForVisit: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_time_range(self) -> "AppointmentBase":
        if self.endTime <= self.startTime:
            raise ValueError("endTime must be after startTime.")
        return self


class AppointmentCreate(AppointmentBase):
    patientId: uuid.UUID
    doctorId: uuid.UUID


class AppointmentUpdate(BaseModel):
    startTime: datetime | None = None
    endTime: datetime | None = None
    status: AppointmentStatus | None = None
    reasonForVisit: str | None = Field(default=None, max_length=2000)


class AppointmentRead(AppointmentBase):
    model_config = ConfigDict(from_attributes=True)

    appointmentId: uuid.UUID
    patientId: uuid.UUID
    doctorId: uuid.UUID
    status: AppointmentStatus
    telehealthRoomId: str | None = None
