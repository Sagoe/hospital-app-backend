"""Vital signs repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vital_signs import VitalSigns


class VitalsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        patient_id: uuid.UUID,
        nurse_id: uuid.UUID,
        blood_pressure_systolic: int,
        blood_pressure_diastolic: int,
        heart_rate: int,
        temperature_celsius,
        respiratory_rate: int,
        oxygen_saturation: int,
        notes: str | None,
    ) -> VitalSigns:
        vital = VitalSigns(
            patientId=patient_id,
            nurseId=nurse_id,
            bloodPressureSystolic=blood_pressure_systolic,
            bloodPressureDiastolic=blood_pressure_diastolic,
            heartRate=heart_rate,
            temperatureCelsius=temperature_celsius,
            respiratoryRate=respiratory_rate,
            oxygenSaturation=oxygen_saturation,
            notes=notes,
        )
        self._session.add(vital)
        await self._session.flush()
        await self._session.refresh(vital)
        return vital

    async def list_by_patient(self, patient_id: uuid.UUID) -> list[VitalSigns]:
        result = await self._session.execute(
            select(VitalSigns)
            .where(VitalSigns.patientId == patient_id)
            .order_by(VitalSigns.recordedAt.desc())
        )
        return list(result.scalars().all())