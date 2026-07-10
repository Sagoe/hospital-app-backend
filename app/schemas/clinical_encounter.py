"""
Pydantic schemas for the Clinical Encounter & Medical Record entity.

`diagnosisText` is plaintext at the API boundary only, mirroring the
pattern used for the patient's national ID — the service layer encrypts
it into `encryptedDiagnosisText` before persistence.
"""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class PrescriptionItem(BaseModel):
    medicationName: str = Field(min_length=1, max_length=200)
    dosage: str = Field(min_length=1, max_length=100)
    frequency: str = Field(min_length=1, max_length=100)
    durationDays: int = Field(ge=1, le=365)
    refillsAllowed: int = Field(ge=0, le=12)
    instructions: str = Field(min_length=1, max_length=1000)


class ClinicalEncounterBase(BaseModel):
    symptoms: str = Field(min_length=1)
    clinicalNotes: str = Field(min_length=1)
    icd10Code: str = Field(min_length=3, max_length=10)
    prescriptionData: list[PrescriptionItem] = Field(default_factory=list)


class ClinicalEncounterCreate(ClinicalEncounterBase):
    appointmentId: uuid.UUID
    patientId: uuid.UUID
    doctorId: uuid.UUID
    diagnosisText: str = Field(min_length=1, description="Plaintext; encrypted before storage.")


class ClinicalEncounterUpdate(BaseModel):
    symptoms: str | None = None
    clinicalNotes: str | None = None
    icd10Code: str | None = Field(default=None, max_length=10)
    prescriptionData: list[PrescriptionItem] | None = None
    diagnosisText: str | None = Field(default=None, description="Plaintext; encrypted before storage.")


class ClinicalEncounterRead(ClinicalEncounterBase):
    model_config = ConfigDict(from_attributes=True)

    encounterId: uuid.UUID
    appointmentId: uuid.UUID
    patientId: uuid.UUID
    doctorId: uuid.UUID
    diagnosisText: str = Field(description="Decrypted plaintext, only populated for authorized callers.")
