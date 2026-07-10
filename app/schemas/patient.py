"""
Pydantic schemas for the Patient Profile entity.

`nationalId` is PLAINTEXT here (API input/output boundary only). The
service layer is solely responsible for calling FieldEncryptionService
to convert it to `encryptedNationalId` before it reaches the repository/
ORM layer, and for decrypting it back out when building `PatientRead`
for an authorized caller. No schema in this file ever holds ciphertext.
"""

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BloodType, Gender


class PatientProfileBase(BaseModel):
    firstName: str = Field(min_length=1, max_length=100)
    lastName: str = Field(min_length=1, max_length=100)
    dateOfBirth: date
    gender: Gender
    phoneNumber: str = Field(min_length=7, max_length=20)
    emergencyContactName: str = Field(min_length=1, max_length=150)
    emergencyContactPhone: str = Field(min_length=7, max_length=20)
    bloodType: BloodType
    insuranceProvider: str | None = Field(default=None, max_length=150)
    insurancePolicyNumber: str | None = Field(default=None, max_length=100)


class PatientProfileCreate(PatientProfileBase):
    nationalId: str = Field(min_length=1, max_length=64, description="Plaintext SSN/insurance ID; encrypted before storage.")


class PatientProfileUpdate(BaseModel):
    firstName: str | None = Field(default=None, max_length=100)
    lastName: str | None = Field(default=None, max_length=100)
    phoneNumber: str | None = Field(default=None, max_length=20)
    emergencyContactName: str | None = Field(default=None, max_length=150)
    emergencyContactPhone: str | None = Field(default=None, max_length=20)
    insuranceProvider: str | None = Field(default=None, max_length=150)
    insurancePolicyNumber: str | None = Field(default=None, max_length=100)


class PatientProfileRead(PatientProfileBase):
    model_config = ConfigDict(from_attributes=True)

    patientId: uuid.UUID
    userId: uuid.UUID
    assignedNurseId: uuid.UUID | None
    assignedDoctorId: uuid.UUID | None
    nationalId: str = Field(description="Decrypted plaintext, only populated for authorized callers.")


class PatientAssignNurseRequest(BaseModel):
    nurseUserId: uuid.UUID


class PatientAssignDoctorRequest(BaseModel):
    doctorUserId: uuid.UUID


class PatientProfileCreateByStaff(PatientProfileCreate):
    userId: uuid.UUID