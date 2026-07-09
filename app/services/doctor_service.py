"""Doctor service — no PHI encryption boundary needed here (doctor
fields are not classified PHI), but still routes all writes through the
repository per the layered-architecture rule."""

import uuid

from app.models.doctor import DoctorProfile
from app.repositories.doctor_repository import DoctorRepository
from app.schemas.doctor import DoctorProfileCreate, DoctorProfileUpdate


class DoctorNotFoundError(Exception):
    pass


class DoctorService:
    def __init__(self, doctor_repository: DoctorRepository) -> None:
        self._doctor_repository = doctor_repository

    async def create_profile(self, user_id: uuid.UUID, payload: DoctorProfileCreate) -> DoctorProfile:
        return await self._doctor_repository.create(
            user_id=user_id,
            specialty=payload.specialty,
            license_number=payload.licenseNumber,
            department_id=payload.departmentId,
            consultation_fee=payload.consultationFee,
        )

    async def get_profile(self, doctor_id: uuid.UUID) -> DoctorProfile:
        doctor = await self._doctor_repository.get_by_id(doctor_id)
        if doctor is None:
            raise DoctorNotFoundError(f"Doctor {doctor_id} not found.")
        return doctor

    async def get_profile_by_user_id(self, user_id: uuid.UUID) -> DoctorProfile:
        doctor = await self._doctor_repository.get_by_user_id(user_id)
        if doctor is None:
            raise DoctorNotFoundError(f"No doctor profile found for user {user_id}.")
        return doctor

    async def list_available(self) -> list[DoctorProfile]:
        return await self._doctor_repository.list_available()

    async def search_by_specialty(self, specialty: str) -> list[DoctorProfile]:
        return await self._doctor_repository.list_by_specialty(specialty)

    async def update_profile(self, doctor_id: uuid.UUID, updates: DoctorProfileUpdate) -> DoctorProfile:
        doctor = await self._doctor_repository.get_by_id(doctor_id)
        if doctor is None:
            raise DoctorNotFoundError(f"Doctor {doctor_id} not found.")
        return await self._doctor_repository.update(doctor, updates)