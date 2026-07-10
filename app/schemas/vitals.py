"""Pydantic schemas for the Vital Signs entity."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VitalSignsBase(BaseModel):
    bloodPressureSystolic: int = Field(ge=40, le=300)
    bloodPressureDiastolic: int = Field(ge=20, le=200)
    heartRate: int = Field(ge=20, le=250)
    temperatureCelsius: float = Field(ge=25.0, le=45.0)
    respiratoryRate: int = Field(ge=5, le=80)
    oxygenSaturation: int = Field(ge=0, le=100)
    notes: str | None = Field(default=None, max_length=1000)


class VitalSignsCreate(VitalSignsBase):
    patientId: uuid.UUID


class VitalSignsRead(VitalSignsBase):
    model_config = ConfigDict(from_attributes=True)

    vitalId: uuid.UUID
    patientId: uuid.UUID
    nurseId: uuid.UUID | None
    recordedAt: datetime