"""Appointment service — scheduling business rules live here, not in the router."""

import uuid

from app.models.appointment import Appointment
from app.models.enums import AppointmentStatus, AppointmentType
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.services.telehealth_service import TelehealthService


class AppointmentNotFoundError(Exception):
    pass


class SchedulingConflictError(Exception):
    pass


class AppointmentService:
    def __init__(
        self,
        appointment_repository: AppointmentRepository,
        telehealth_service: TelehealthService,
    ) -> None:
        self._appointment_repository = appointment_repository
        self._telehealth_service = telehealth_service

    async def create_appointment(self, payload: AppointmentCreate) -> Appointment:
        overlapping = await self._appointment_repository.find_overlapping_for_doctor(
            payload.doctorId, payload.startTime, payload.endTime
        )
        if overlapping:
            raise SchedulingConflictError(
                "The selected doctor already has an appointment in this time window."
            )

        appointment = await self._appointment_repository.create(
            patient_id=payload.patientId,
            doctor_id=payload.doctorId,
            start_time=payload.startTime,
            end_time=payload.endTime,
            appointment_type=payload.appointmentType,
            reason_for_visit=payload.reasonForVisit,
        )

        if payload.appointmentType == AppointmentType.TELEHEALTH:
            room_sid = await self._telehealth_service.create_video_room(appointment.appointmentId)
            appointment.telehealthRoomId = room_sid
            appointment = await self._appointment_repository.update(
                appointment, AppointmentUpdate()
            )

        return appointment

    async def get_appointment(self, appointment_id: uuid.UUID) -> Appointment:
        appointment = await self._appointment_repository.get_by_id(appointment_id)
        if appointment is None:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found.")
        return appointment

    async def list_for_patient(self, patient_id: uuid.UUID) -> list[Appointment]:
        return await self._appointment_repository.list_by_patient(patient_id)

    async def list_for_doctor(self, doctor_id: uuid.UUID) -> list[Appointment]:
        return await self._appointment_repository.list_by_doctor(doctor_id)

    async def update_status(
        self, appointment_id: uuid.UUID, new_status: AppointmentStatus
    ) -> Appointment:
        appointment = await self.get_appointment(appointment_id)
        return await self._appointment_repository.update(
            appointment, AppointmentUpdate(status=new_status)
        )

    async def reschedule(
        self, appointment_id: uuid.UUID, updates: AppointmentUpdate
    ) -> Appointment:
        appointment = await self.get_appointment(appointment_id)

        if updates.startTime and updates.endTime:
            overlapping = await self._appointment_repository.find_overlapping_for_doctor(
                appointment.doctorId, updates.startTime, updates.endTime
            )
            overlapping_excluding_self = [
                a for a in overlapping if a.appointmentId != appointment_id
            ]
            if overlapping_excluding_self:
                raise SchedulingConflictError(
                    "The selected doctor already has an appointment in this time window."
                )

        return await self._appointment_repository.update(appointment, updates)
