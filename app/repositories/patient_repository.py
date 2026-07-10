"""
Patient repository.

IMPORTANT: this layer only ever sees `encryptedNationalId` ciphertext.
Encryption/decryption happens exclusively in PatientService — the
repository has no dependency on FieldEncryptionService by design, so it
cannot accidentally persist plaintext PHI.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import PatientProfile
from app.schemas.patient import PatientProfileUpdate


class PatientRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, patient_id: uuid.UUID) -> PatientProfile | None:
        result = await self._session.execute(
            select(PatientProfile).where(PatientProfile.patientId == patient_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> PatientProfile | None:
        result = await self._session.execute(
            select(PatientProfile).where(PatientProfile.userId == user_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        first_name: str,
        last_name: str,
        date_of_birth,
        gender,
        phone_number: str,
        emergency_contact_name: str,
        emergency_contact_phone: str,
        blood_type,
        encrypted_national_id: str,
        insurance_provider: str | None,
        insurance_policy_number: str | None,
    ) -> PatientProfile:
        patient = PatientProfile(
            userId=user_id,
            firstName=first_name,
            lastName=last_name,
            dateOfBirth=date_of_birth,
            gender=gender,
            phoneNumber=phone_number,
            emergencyContactName=emergency_contact_name,
            emergencyContactPhone=emergency_contact_phone,
            bloodType=blood_type,
            encryptedNationalId=encrypted_national_id,
            insuranceProvider=insurance_provider,
            insurancePolicyNumber=insurance_policy_number,
        )
        self._session.add(patient)
        await self._session.flush()
        await self._session.refresh(patient)
        return patient

    async def update(self, patient: PatientProfile, updates: PatientProfileUpdate) -> PatientProfile:
        for field, value in updates.model_dump(exclude_unset=True).items():
            setattr(patient, field, value)
        await self._session.flush()
        await self._session.refresh(patient)
        return patient

    async def assign_nurse(self, patient: PatientProfile, nurse_user_id: uuid.UUID) -> PatientProfile:
        patient.assignedNurseId = nurse_user_id
        await self._session.flush()
        await self._session.refresh(patient)
        return patient

    async def assign_doctor(self, patient: PatientProfile, doctor_user_id: uuid.UUID) -> PatientProfile:
        patient.assignedDoctorId = doctor_user_id
        await self._session.flush()
        await self._session.refresh(patient)
        return patient

    async def list_by_assigned_nurse(self, nurse_user_id: uuid.UUID) -> list[PatientProfile]:
        result = await self._session.execute(
            select(PatientProfile).where(PatientProfile.assignedNurseId == nurse_user_id)
        )
        return list(result.scalars().all())

    async def list_by_assigned_doctor(self, doctor_user_id: uuid.UUID) -> list[PatientProfile]:
        result = await self._session.execute(
            select(PatientProfile).where(PatientProfile.assignedDoctorId == doctor_user_id)
        )
        return list(result.scalars().all())

    async def list_unassigned_to_nurse(self) -> list[PatientProfile]:
        result = await self._session.execute(
            select(PatientProfile).where(PatientProfile.assignedNurseId.is_(None))
        )
        return list(result.scalars().all())