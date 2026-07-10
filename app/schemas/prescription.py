"""Pydantic schemas for the Prescription entity (pharmacy workflow)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PrescriptionStatus


class PrescriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prescriptionId: uuid.UUID
    encounterId: uuid.UUID
    patientId: uuid.UUID
    doctorId: uuid.UUID
    medicationName: str
    dosage: str
    frequency: str
    durationDays: int
    instructions: str | None
    status: PrescriptionStatus
    fulfilledByUserId: uuid.UUID | None
    fulfilledAt: datetime | None
    prescribedAt: datetime