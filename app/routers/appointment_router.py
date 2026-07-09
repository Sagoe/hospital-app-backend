"""Appointment router."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUser, get_appointment_service, require_role
from app.models.enums import AppointmentStatus, UserRole
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentUpdate
from app.services.appointment_service import (
    AppointmentNotFoundError,
    AppointmentService,
    SchedulingConflictError,
)

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate,
    current_user: CurrentUser,
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> AppointmentRead:
    try:
        appointment = await appointment_service.create_appointment(payload)
    except SchedulingConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return AppointmentRead.model_validate(appointment)


@router.get("/patient/{patient_id}", response_model=list[AppointmentRead])
async def list_appointments_for_patient(
    patient_id: uuid.UUID,
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> list[AppointmentRead]:
    appointments = await appointment_service.list_for_patient(patient_id)
    return [AppointmentRead.model_validate(a) for a in appointments]


@router.get("/doctor/{doctor_id}", response_model=list[AppointmentRead])
async def list_appointments_for_doctor(
    doctor_id: uuid.UUID,
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> list[AppointmentRead]:
    appointments = await appointment_service.list_for_doctor(doctor_id)
    return [AppointmentRead.model_validate(a) for a in appointments]


@router.get("/{appointment_id}", response_model=AppointmentRead)
async def get_appointment(
    appointment_id: uuid.UUID,
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> AppointmentRead:
    try:
        appointment = await appointment_service.get_appointment(appointment_id)
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AppointmentRead.model_validate(appointment)


@router.patch("/{appointment_id}", response_model=AppointmentRead)
async def reschedule_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentUpdate,
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> AppointmentRead:
    try:
        appointment = await appointment_service.reschedule(appointment_id, payload)
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SchedulingConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return AppointmentRead.model_validate(appointment)


@router.post(
    "/{appointment_id}/check-in",
    response_model=AppointmentRead,
    dependencies=[Depends(require_role(UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN))],
)
async def check_in_appointment(
    appointment_id: uuid.UUID,
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> AppointmentRead:
    try:
        appointment = await appointment_service.update_status(
            appointment_id, AppointmentStatus.CHECKED_IN
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AppointmentRead.model_validate(appointment)


@router.post("/{appointment_id}/cancel", response_model=AppointmentRead)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    appointment_service: AppointmentService = Depends(get_appointment_service),
) -> AppointmentRead:
    try:
        appointment = await appointment_service.update_status(
            appointment_id, AppointmentStatus.CANCELLED
        )
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AppointmentRead.model_validate(appointment)
