"""
Patient router.

Access rule: a PATIENT may only read/update their own profile. DOCTOR,
NURSE, and ADMIN roles may access any patient profile (clinical need /
administrative oversight), with every access still audited by
PatientService.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import (
    CurrentUser,
    get_client_ip,
    get_patient_service,
)
from app.models.enums import UserRole
from app.schemas.patient import PatientProfileCreate, PatientProfileRead, PatientProfileUpdate
from app.services.patient_service import PatientNotFoundError, PatientService

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


def _assert_can_access_patient(current_user, patient: PatientProfileRead) -> None:
    if current_user.role == UserRole.PATIENT and patient.userId != current_user.userId:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patients may only access their own medical profile.",
        )


@router.post("", response_model=PatientProfileRead, status_code=status.HTTP_201_CREATED)
async def create_patient_profile(
    payload: PatientProfileCreate,
    current_user: CurrentUser,
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientProfileRead:
    if current_user.role != UserRole.PATIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a patient account may create its own patient profile.",
        )
    return await patient_service.create_profile(current_user.userId, payload)


# NOTE: "/me" must be declared BEFORE "/{patient_id}" — otherwise FastAPI
# routes GET /patients/me into get_patient_profile and tries (and fails)
# to parse the literal string "me" as a UUID, producing a 422.
@router.get("/me", response_model=PatientProfileRead)
async def get_my_patient_profile(
    request: Request,
    current_user: CurrentUser,
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientProfileRead:
    try:
        return await patient_service.get_profile_by_user_id(
            current_user.userId, get_client_ip(request)
        )
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{patient_id}", response_model=PatientProfileRead)
async def get_patient_profile(
    patient_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientProfileRead:
    try:
        patient = await patient_service.get_profile(
            patient_id, current_user.userId, get_client_ip(request)
        )
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    _assert_can_access_patient(current_user, patient)
    return patient


@router.patch("/{patient_id}", response_model=PatientProfileRead)
async def update_patient_profile(
    patient_id: uuid.UUID,
    payload: PatientProfileUpdate,
    request: Request,
    current_user: CurrentUser,
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientProfileRead:
    try:
        existing = await patient_service.get_profile(
            patient_id, current_user.userId, get_client_ip(request)
        )
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    _assert_can_access_patient(current_user, existing)

    try:
        return await patient_service.update_profile(
            patient_id, payload, current_user.userId, get_client_ip(request)
        )
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc