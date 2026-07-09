"""
Clinical Encounter service.

Mirrors PatientService's pattern: this is the only layer that holds
plaintext diagnosis text in memory, and it is responsible for the
READ_PHI / WRITE_PHI audit trail around clinical records.
"""

import uuid

from app.core.encryption import FieldEncryptionService
from app.models.clinical_encounter import ClinicalEncounter
from app.models.enums import AuditActionType
from app.repositories.clinical_encounter_repository import ClinicalEncounterRepository
from app.schemas.clinical_encounter import (
    ClinicalEncounterCreate,
    ClinicalEncounterRead,
    ClinicalEncounterUpdate,
)
from app.services.audit_service import AuditService


class EncounterNotFoundError(Exception):
    pass


class ClinicalEncounterService:
    def __init__(
        self,
        encounter_repository: ClinicalEncounterRepository,
        encryption_service: FieldEncryptionService,
        audit_service: AuditService,
    ) -> None:
        self._encounter_repository = encounter_repository
        self._encryption_service = encryption_service
        self._audit_service = audit_service

    async def create_encounter(
        self, payload: ClinicalEncounterCreate, requesting_user_id: uuid.UUID, ip_address: str
    ) -> ClinicalEncounterRead:
        encrypted_diagnosis = self._encryption_service.encrypt(payload.diagnosisText)

        encounter = await self._encounter_repository.create(
            appointment_id=payload.appointmentId,
            patient_id=payload.patientId,
            doctor_id=payload.doctorId,
            symptoms=payload.symptoms,
            clinical_notes=payload.clinicalNotes,
            icd10_code=payload.icd10Code,
            prescription_data=[item.model_dump() for item in payload.prescriptionData],
            encrypted_diagnosis_text=encrypted_diagnosis,
        )

        await self._audit_service.record(
            performed_by_user_id=requesting_user_id,
            action_type=AuditActionType.WRITE_PHI,
            target_record_id=encounter.encounterId,
            target_table="clinical_encounters",
            ip_address=ip_address,
        )

        return self._to_read_schema(encounter, payload.diagnosisText)

    async def get_encounter(
        self, encounter_id: uuid.UUID, requesting_user_id: uuid.UUID, ip_address: str
    ) -> ClinicalEncounterRead:
        encounter = await self._encounter_repository.get_by_id(encounter_id)
        if encounter is None:
            raise EncounterNotFoundError(f"Encounter {encounter_id} not found.")

        plaintext_diagnosis = self._encryption_service.decrypt(encounter.encryptedDiagnosisText)

        await self._audit_service.record(
            performed_by_user_id=requesting_user_id,
            action_type=AuditActionType.READ_PHI,
            target_record_id=encounter.encounterId,
            target_table="clinical_encounters",
            ip_address=ip_address,
        )

        return self._to_read_schema(encounter, plaintext_diagnosis)

    async def list_for_patient(
        self, patient_id: uuid.UUID, requesting_user_id: uuid.UUID, ip_address: str
    ) -> list[ClinicalEncounterRead]:
        encounters = await self._encounter_repository.list_by_patient(patient_id)

        results = []
        for encounter in encounters:
            plaintext_diagnosis = self._encryption_service.decrypt(encounter.encryptedDiagnosisText)
            await self._audit_service.record(
                performed_by_user_id=requesting_user_id,
                action_type=AuditActionType.READ_PHI,
                target_record_id=encounter.encounterId,
                target_table="clinical_encounters",
                ip_address=ip_address,
            )
            results.append(self._to_read_schema(encounter, plaintext_diagnosis))
        return results

    async def update_encounter(
        self,
        encounter_id: uuid.UUID,
        updates: ClinicalEncounterUpdate,
        requesting_user_id: uuid.UUID,
        ip_address: str,
    ) -> ClinicalEncounterRead:
        encounter = await self._encounter_repository.get_by_id(encounter_id)
        if encounter is None:
            raise EncounterNotFoundError(f"Encounter {encounter_id} not found.")

        encrypted_diagnosis = (
            self._encryption_service.encrypt(updates.diagnosisText)
            if updates.diagnosisText is not None
            else None
        )

        updated = await self._encounter_repository.update(encounter, updates, encrypted_diagnosis)
        plaintext_diagnosis = self._encryption_service.decrypt(updated.encryptedDiagnosisText)

        await self._audit_service.record(
            performed_by_user_id=requesting_user_id,
            action_type=AuditActionType.WRITE_PHI,
            target_record_id=updated.encounterId,
            target_table="clinical_encounters",
            ip_address=ip_address,
        )

        return self._to_read_schema(updated, plaintext_diagnosis)

    @staticmethod
    def _to_read_schema(
        encounter: ClinicalEncounter, plaintext_diagnosis: str
    ) -> ClinicalEncounterRead:
        return ClinicalEncounterRead(
            encounterId=encounter.encounterId,
            appointmentId=encounter.appointmentId,
            patientId=encounter.patientId,
            doctorId=encounter.doctorId,
            symptoms=encounter.symptoms,
            clinicalNotes=encounter.clinicalNotes,
            icd10Code=encounter.icd10Code,
            prescriptionData=encounter.prescriptionData,
            diagnosisText=plaintext_diagnosis,
        )
