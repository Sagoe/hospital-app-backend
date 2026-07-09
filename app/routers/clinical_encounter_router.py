"""
Clinical Encounter router.

Only clinical staff (DOCTOR, NURSE) may create/update medical records.
A PATIENT may read their own encounters; ADMIN has oversight read access.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import (
    CurrentUser,
    get_client_ip,
    get_encounter_service,
    get_patient_service,
    require_role,
)
from app.models.enums import UserRole
from app.schemas.clinical_encounter import (
    ClinicalEncounterCreate,
    ClinicalEncounterRead,
    ClinicalEncounterUpdate,
)
from app.services.clinical_encounter_service import ClinicalEncounterService, EncounterNotFoundError
from app.services.patient_service import PatientService

router = APIRouter(prefix="/api/v1/encounters", tags=["clinical-encounters"])


async def _resolve_own_patient_id(current_user: CurrentUser, patient_service: PatientService) -> uuid.UUID:
    """For a PATIENT-role caller, resolves their own patientId (the FK
    used on encounters/appointments) from their userId (the JWT subject).
    Raises 403 if no patient profile exists yet."""
    patient_id = await patient_service.get_patient_id_for_user(current_user.userId)
    if patient_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No patient profile is associated with this account.",
        )
    return patient_id


@router.post(
    "",
    response_model=ClinicalEncounterRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.DOCTOR, UserRole.NURSE))],
)
async def create_encounter(
    payload: ClinicalEncounterCreate,
    request: Request,
    current_user: CurrentUser,
    encounter_service: ClinicalEncounterService = Depends(get_encounter_service),
) -> ClinicalEncounterRead:
    return await encounter_service.create_encounter(
        payload, current_user.userId, get_client_ip(request)
    )


@router.get("/{encounter_id}", response_model=ClinicalEncounterRead)
async def get_encounter(
    encounter_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    encounter_service: ClinicalEncounterService = Depends(get_encounter_service),
    patient_service: PatientService = Depends(get_patient_service),
) -> ClinicalEncounterRead:
    try:
        encounter = await encounter_service.get_encounter(
            encounter_id, current_user.userId, get_client_ip(request)
        )
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if current_user.role == UserRole.PATIENT:
        own_patient_id = await _resolve_own_patient_id(current_user, patient_service)
        if encounter.patientId != own_patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients may only access their own medical records.",
            )
    return encounter


@router.get("/patient/{patient_id}", response_model=list[ClinicalEncounterRead])
async def list_encounters_for_patient(
    patient_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    encounter_service: ClinicalEncounterService = Depends(get_encounter_service),
    patient_service: PatientService = Depends(get_patient_service),
) -> list[ClinicalEncounterRead]:
    if current_user.role == UserRole.PATIENT:
        own_patient_id = await _resolve_own_patient_id(current_user, patient_service)
        if patient_id != own_patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients may only access their own medical records.",
            )
    return await encounter_service.list_for_patient(
        patient_id, current_user.userId, get_client_ip(request)
    )


@router.patch(
    "/{encounter_id}",
    response_model=ClinicalEncounterRead,
    dependencies=[Depends(require_role(UserRole.DOCTOR, UserRole.NURSE))],
)
async def update_encounter(
    encounter_id: uuid.UUID,
    payload: ClinicalEncounterUpdate,
    request: Request,
    current_user: CurrentUser,
    encounter_service: ClinicalEncounterService = Depends(get_encounter_service),
) -> ClinicalEncounterRead:
    try:
        return await encounter_service.update_encounter(
            encounter_id, payload, current_user.userId, get_client_ip(request)
        )
    except EncounterNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
