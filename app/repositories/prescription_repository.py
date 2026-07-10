"""Prescription repository — pharmacy workflow."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PrescriptionStatus
from app.models.prescription import Prescription


class PrescriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        encounter_id: uuid.UUID,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        medication_name: str,
        dosage: str,
        frequency: str,
        duration_days: int,
        instructions: str | None,
    ) -> Prescription:
        prescription = Prescription(
            encounterId=encounter_id,
            patientId=patient_id,
            doctorId=doctor_id,
            medicationName=medication_name,
            dosage=dosage,
            frequency=frequency,
            durationDays=duration_days,
            instructions=instructions,
        )
        self._session.add(prescription)
        await self._session.flush()
        await self._session.refresh(prescription)
        return prescription

    async def get_by_id(self, prescription_id: uuid.UUID) -> Prescription | None:
        result = await self._session.execute(
            select(Prescription).where(Prescription.prescriptionId == prescription_id)
        )
        return result.scalar_one_or_none()

    async def list_pending(self) -> list[Prescription]:
        result = await self._session.execute(
            select(Prescription)
            .where(Prescription.status == PrescriptionStatus.PENDING)
            .order_by(Prescription.prescribedAt.asc())
        )
        return list(result.scalars().all())

    async def list_by_patient(self, patient_id: uuid.UUID) -> list[Prescription]:
        result = await self._session.execute(
            select(Prescription)
            .where(Prescription.patientId == patient_id)
            .order_by(Prescription.prescribedAt.desc())
        )
        return list(result.scalars().all())

    async def fulfill(self, prescription: Prescription, fulfilled_by_user_id: uuid.UUID) -> Prescription:
        prescription.status = PrescriptionStatus.FULFILLED
        prescription.fulfilledByUserId = fulfilled_by_user_id
        prescription.fulfilledAt = datetime.now(timezone.utc)
        await self._session.flush()
        await self._session.refresh(prescription)
        return prescription