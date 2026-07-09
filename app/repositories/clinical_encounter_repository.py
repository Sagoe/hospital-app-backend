"""Clinical Encounter repository. Like PatientRepository, this layer only
ever handles `encryptedDiagnosisText` ciphertext — encryption/decryption
is owned exclusively by ClinicalEncounterService."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinical_encounter import ClinicalEncounter
from app.schemas.clinical_encounter import ClinicalEncounterUpdate


class ClinicalEncounterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, encounter_id: uuid.UUID) -> ClinicalEncounter | None:
        result = await self._session.execute(
            select(ClinicalEncounter).where(ClinicalEncounter.encounterId == encounter_id)
        )
        return result.scalar_one_or_none()

    async def get_by_appointment_id(self, appointment_id: uuid.UUID) -> ClinicalEncounter | None:
        result = await self._session.execute(
            select(ClinicalEncounter).where(ClinicalEncounter.appointmentId == appointment_id)
        )
        return result.scalar_one_or_none()

    async def list_by_patient(self, patient_id: uuid.UUID) -> list[ClinicalEncounter]:
        result = await self._session.execute(
            select(ClinicalEncounter).where(ClinicalEncounter.patientId == patient_id)
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        appointment_id: uuid.UUID,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        symptoms: str,
        clinical_notes: str,
        icd10_code: str,
        prescription_data: list[dict],
        encrypted_diagnosis_text: str,
    ) -> ClinicalEncounter:
        encounter = ClinicalEncounter(
            appointmentId=appointment_id,
            patientId=patient_id,
            doctorId=doctor_id,
            symptoms=symptoms,
            clinicalNotes=clinical_notes,
            icd10Code=icd10_code,
            prescriptionData=prescription_data,
            encryptedDiagnosisText=encrypted_diagnosis_text,
        )
        self._session.add(encounter)
        await self._session.flush()
        await self._session.refresh(encounter)
        return encounter

    async def update(
        self, encounter: ClinicalEncounter, updates: ClinicalEncounterUpdate, encrypted_diagnosis_text: str | None
    ) -> ClinicalEncounter:
        data = updates.model_dump(exclude_unset=True, exclude={"diagnosisText", "prescriptionData"})
        for field, value in data.items():
            setattr(encounter, field, value)
        if updates.prescriptionData is not None:
            encounter.prescriptionData = [item.model_dump() for item in updates.prescriptionData]
        if encrypted_diagnosis_text is not None:
            encounter.encryptedDiagnosisText = encrypted_diagnosis_text
        await self._session.flush()
        await self._session.refresh(encounter)
        return encounter
