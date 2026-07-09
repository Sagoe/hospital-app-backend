"""Appointment repository."""

import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus
from app.schemas.appointment import AppointmentUpdate


class AppointmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, appointment_id: uuid.UUID) -> Appointment | None:
        result = await self._session.execute(
            select(Appointment).where(Appointment.appointmentId == appointment_id)
        )
        return result.scalar_one_or_none()

    async def list_by_patient(self, patient_id: uuid.UUID) -> list[Appointment]:
        result = await self._session.execute(
            select(Appointment)
            .where(Appointment.patientId == patient_id)
            .order_by(Appointment.startTime.desc())
        )
        return list(result.scalars().all())

    async def list_by_doctor(self, doctor_id: uuid.UUID) -> list[Appointment]:
        result = await self._session.execute(
            select(Appointment)
            .where(Appointment.doctorId == doctor_id)
            .order_by(Appointment.startTime.desc())
        )
        return list(result.scalars().all())

    async def find_overlapping_for_doctor(
        self, doctor_id: uuid.UUID, start_time: datetime, end_time: datetime
    ) -> list[Appointment]:
        """Used by AppointmentService to reject double-bookings. Overlap
        test: existing.start < new.end AND existing.end > new.start,
        excluding cancelled/no-show appointments which no longer hold the slot."""
        result = await self._session.execute(
            select(Appointment).where(
                and_(
                    Appointment.doctorId == doctor_id,
                    Appointment.status.not_in(
                        [AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]
                    ),
                    Appointment.startTime < end_time,
                    Appointment.endTime > start_time,
                )
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        patient_id: uuid.UUID,
        doctor_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        appointment_type,
        reason_for_visit: str,
        telehealth_room_id: str | None = None,
    ) -> Appointment:
        appointment = Appointment(
            patientId=patient_id,
            doctorId=doctor_id,
            startTime=start_time,
            endTime=end_time,
            appointmentType=appointment_type,
            reasonForVisit=reason_for_visit,
            telehealthRoomId=telehealth_room_id,
        )
        self._session.add(appointment)
        await self._session.flush()
        await self._session.refresh(appointment)
        return appointment

    async def update(self, appointment: Appointment, updates: AppointmentUpdate) -> Appointment:
        for field, value in updates.model_dump(exclude_unset=True).items():
            setattr(appointment, field, value)
        await self._session.flush()
        await self._session.refresh(appointment)
        return appointment
