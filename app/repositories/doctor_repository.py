"""Doctor repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import DoctorProfile
from app.models.enums import AvailabilityStatus
from app.schemas.doctor import DoctorProfileUpdate


class DoctorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, doctor_id: uuid.UUID) -> DoctorProfile | None:
        result = await self._session.execute(
            select(DoctorProfile).where(DoctorProfile.doctorId == doctor_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> DoctorProfile | None:
        result = await self._session.execute(
            select(DoctorProfile).where(DoctorProfile.userId == user_id)
        )
        return result.scalar_one_or_none()

    async def list_by_specialty(self, specialty: str) -> list[DoctorProfile]:
        result = await self._session.execute(
            select(DoctorProfile).where(DoctorProfile.specialty.ilike(f"%{specialty}%"))
        )
        return list(result.scalars().all())

    async def list_available(self) -> list[DoctorProfile]:
        result = await self._session.execute(
            select(DoctorProfile).where(
                DoctorProfile.availabilityStatus == AvailabilityStatus.AVAILABLE
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        specialty: str,
        license_number: str,
        department_id: uuid.UUID | None,
        consultation_fee,
    ) -> DoctorProfile:
        doctor = DoctorProfile(
            userId=user_id,
            specialty=specialty,
            licenseNumber=license_number,
            departmentId=department_id,
            consultationFee=consultation_fee,
        )
        self._session.add(doctor)
        await self._session.flush()
        await self._session.refresh(doctor)
        return doctor

    async def update(self, doctor: DoctorProfile, updates: DoctorProfileUpdate) -> DoctorProfile:
        for field, value in updates.model_dump(exclude_unset=True).items():
            setattr(doctor, field, value)
        await self._session.flush()
        await self._session.refresh(doctor)
        return doctor
