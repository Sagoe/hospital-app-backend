"""
Patient service.

This is the ONLY layer permitted to hold a plaintext national ID in
memory. It encrypts before calling the repository and decrypts after
reading from it, and it is responsible for emitting READ_PHI /
WRITE_PHI audit events around those operations.
"""

import uuid

from app.core.encryption import FieldEncryptionService
from app.models.enums import AuditActionType
from app.models.patient import PatientProfile
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientProfileCreate, PatientProfileRead, PatientProfileUpdate
from app.services.audit_service import AuditService


class PatientNotFoundError(Exception):
    pass


class PatientService:
    def __init__(
        self,
        patient_repository: PatientRepository,
        encryption_service: FieldEncryptionService,
        audit_service: AuditService,
    ) -> None:
        self._patient_repository = patient_repository
        self._encryption_service = encryption_service
        self._audit_service = audit_service

    async def create_profile(
        self, user_id: uuid.UUID, payload: PatientProfileCreate
    ) -> PatientProfileRead:
        encrypted_national_id = self._encryption_service.encrypt(payload.nationalId)

        patient = await self._patient_repository.create(
            user_id=user_id,
            first_name=payload.firstName,
            last_name=payload.lastName,
            date_of_birth=payload.dateOfBirth,
            gender=payload.gender,
            phone_number=payload.phoneNumber,
            emergency_contact_name=payload.emergencyContactName,
            emergency_contact_phone=payload.emergencyContactPhone,
            blood_type=payload.bloodType,
            encrypted_national_id=encrypted_national_id,
            insurance_provider=payload.insuranceProvider,
            insurance_policy_number=payload.insurancePolicyNumber,
        )

        await self._audit_service.record(
            performed_by_user_id=user_id,
            action_type=AuditActionType.WRITE_PHI,
            target_record_id=patient.patientId,
            target_table="patient_profiles",
            ip_address="unknown",  # overwritten by router with the real request IP
        )

        return self._to_read_schema(patient, payload.nationalId)

    async def get_profile(
        self, patient_id: uuid.UUID, requesting_user_id: uuid.UUID, ip_address: str
    ) -> PatientProfileRead:
        patient = await self._patient_repository.get_by_id(patient_id)
        if patient is None:
            raise PatientNotFoundError(f"Patient {patient_id} not found.")

        plaintext_national_id = self._encryption_service.decrypt(patient.encryptedNationalId)

        await self._audit_service.record(
            performed_by_user_id=requesting_user_id,
            action_type=AuditActionType.READ_PHI,
            target_record_id=patient.patientId,
            target_table="patient_profiles",
            ip_address=ip_address,
        )

        return self._to_read_schema(patient, plaintext_national_id)

    async def get_profile_by_user_id(
        self, user_id: uuid.UUID, ip_address: str
    ) -> PatientProfileRead:
        """Used by /patients/me — resolves the caller's own profile via
        userId rather than the patientId primary key."""
        patient = await self._patient_repository.get_by_user_id(user_id)
        if patient is None:
            raise PatientNotFoundError(f"No patient profile found for user {user_id}.")

        plaintext_national_id = self._encryption_service.decrypt(patient.encryptedNationalId)

        await self._audit_service.record(
            performed_by_user_id=user_id,
            action_type=AuditActionType.READ_PHI,
            target_record_id=patient.patientId,
            target_table="patient_profiles",
            ip_address=ip_address,
        )

        return self._to_read_schema(patient, plaintext_national_id)

    async def update_profile(
        self, patient_id: uuid.UUID, updates: PatientProfileUpdate, requesting_user_id: uuid.UUID, ip_address: str
    ) -> PatientProfileRead:
        patient = await self._patient_repository.get_by_id(patient_id)
        if patient is None:
            raise PatientNotFoundError(f"Patient {patient_id} not found.")

        updated = await self._patient_repository.update(patient, updates)
        plaintext_national_id = self._encryption_service.decrypt(updated.encryptedNationalId)

        await self._audit_service.record(
            performed_by_user_id=requesting_user_id,
            action_type=AuditActionType.WRITE_PHI,
            target_record_id=updated.patientId,
            target_table="patient_profiles",
            ip_address=ip_address,
        )

        return self._to_read_schema(updated, plaintext_national_id)

    async def get_patient_id_for_user(self, user_id: uuid.UUID) -> uuid.UUID | None:
        """Resolves a userId to its associated patientId, used by other
        routers/services that need to check 'does this record belong to
        the calling patient' without duplicating repository access."""
        patient = await self._patient_repository.get_by_user_id(user_id)
        return patient.patientId if patient is not None else None

    @staticmethod
    def _to_read_schema(patient: PatientProfile, plaintext_national_id: str) -> PatientProfileRead:
        return PatientProfileRead(
            patientId=patient.patientId,
            userId=patient.userId,
            firstName=patient.firstName,
            lastName=patient.lastName,
            dateOfBirth=patient.dateOfBirth,
            gender=patient.gender,
            phoneNumber=patient.phoneNumber,
            emergencyContactName=patient.emergencyContactName,
            emergencyContactPhone=patient.emergencyContactPhone,
            bloodType=patient.bloodType,
            nationalId=plaintext_national_id,
            insuranceProvider=patient.insuranceProvider,
            insurancePolicyNumber=patient.insurancePolicyNumber,
        )