"""
Patient router.

Access rule: a PATIENT may only read/update their own profile. DOCTOR,
NURSE, and ADMIN roles may access any patient profile (clinical need /
administrative oversight), with every access still audited by
PatientService. RECEPTIONIST assigns a nurse to a newly created
patient; NURSE assigns a doctor to their assigned patients.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import (
    CurrentUser,
    get_auth_service,
    get_client_ip,
    get_patient_service,
    require_role,
)
from app.models.enums import UserRole
from app.schemas.patient import (
    PatientAssignDoctorRequest,
    PatientAssignNurseRequest,
    PatientProfileCreate,
    PatientProfileCreateByStaff,
    PatientProfileRead,
    PatientProfileUpdate,
)
from app.schemas.user import UserRead
from app.services.auth_service import AuthService
from app.services.patient_service import PatientNotFoundError, PatientService
from app.schemas.patient import PatientIntakeCreate  # add alongside existing patient schema imports
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthError, AuthService

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


@router.post(
    "/staff-create",
    response_model=PatientProfileRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.RECEPTIONIST, UserRole.ADMIN))],
)
async def create_patient_profile_by_staff(
    payload: PatientProfileCreateByStaff,
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientProfileRead:
    # payload is a PatientProfileCreateByStaff, which carries an extra
    # `userId` field not present on PatientProfileCreate. We strip it
    # here and pass a plain PatientProfileCreate into the shared
    # service method, so create_profile() never has to know or care
    # that this call originated from staff rather than self-registration —
    # this avoids a duplicate-keyword collision if create_profile()
    # spreads payload.model_dump() into the ORM constructor internally.
    base_payload = PatientProfileCreate(**payload.model_dump(exclude={"userId"}))
    return await patient_service.create_profile(payload.userId, base_payload)


# NOTE: "/me", "/queue/unassigned", "/my-nurse-patients",
# "/my-doctor-patients", and "/staff/nurses" must all be declared
# BEFORE "/{patient_id}" — otherwise FastAPI tries to parse those
# literal path segments as a UUID and fails with a 422.
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


@router.get(
    "/queue/unassigned",
    response_model=list[PatientProfileRead],
    dependencies=[Depends(require_role(UserRole.RECEPTIONIST, UserRole.ADMIN))],
)
async def list_unassigned_patients(
    patient_service: PatientService = Depends(get_patient_service),
) -> list[PatientProfileRead]:
    return await patient_service.list_unassigned_to_nurse()


@router.get(
    "/my-nurse-patients",
    response_model=list[PatientProfileRead],
    dependencies=[Depends(require_role(UserRole.NURSE))],
)
async def list_my_nurse_patients(
    current_user: CurrentUser,
    patient_service: PatientService = Depends(get_patient_service),
) -> list[PatientProfileRead]:
    return await patient_service.list_for_nurse(current_user.userId)


@router.get(
    "/my-doctor-patients",
    response_model=list[PatientProfileRead],
    dependencies=[Depends(require_role(UserRole.DOCTOR))],
)
async def list_my_doctor_patients(
    current_user: CurrentUser,
    patient_service: PatientService = Depends(get_patient_service),
) -> list[PatientProfileRead]:
    return await patient_service.list_for_doctor(current_user.userId)


@router.get(
    "/staff/nurses",
    response_model=list[UserRead],
    dependencies=[Depends(require_role(UserRole.RECEPTIONIST, UserRole.ADMIN))],
)
async def list_nurses(
    auth_service: AuthService = Depends(get_auth_service),
) -> list[UserRead]:
    """Directory lookup so a receptionist can pick a real nurse
    userId when assigning a newly onboarded patient."""
    nurses = await auth_service.list_users_by_role(UserRole.NURSE)
    return [UserRead.model_validate(nurse) for nurse in nurses]


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


@router.patch(
    "/{patient_id}/assign-nurse",
    response_model=PatientProfileRead,
    dependencies=[Depends(require_role(UserRole.RECEPTIONIST, UserRole.ADMIN))],
)
async def assign_nurse_to_patient(
    patient_id: uuid.UUID,
    payload: PatientAssignNurseRequest,
    request: Request,
    current_user: CurrentUser,
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientProfileRead:
    try:
        return await patient_service.assign_nurse(
            patient_id, payload.nurseUserId, current_user.userId, get_client_ip(request)
        )
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch(
    "/{patient_id}/assign-doctor",
    response_model=PatientProfileRead,
    dependencies=[Depends(require_role(UserRole.NURSE, UserRole.ADMIN))],
)
async def assign_doctor_to_patient(
    patient_id: uuid.UUID,
    payload: PatientAssignDoctorRequest,
    request: Request,
    current_user: CurrentUser,
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientProfileRead:
    try:
        return await patient_service.assign_doctor(
            patient_id, payload.doctorUserId, current_user.userId, get_client_ip(request)
        )
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    
@router.post(
    "/staff-intake",
    response_model=PatientProfileRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.RECEPTIONIST, UserRole.ADMIN))],
)
async def create_patient_intake(
    payload: PatientIntakeCreate,
    auth_service: AuthService = Depends(get_auth_service),
    patient_service: PatientService = Depends(get_patient_service),
) -> PatientProfileRead:
    try:
        user = await auth_service.register_staff(
            UserCreate(email=payload.email, password=payload.password, role=UserRole.PATIENT)
        )
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    base_payload = PatientProfileCreate(**payload.model_dump(exclude={"email", "password"}))
    return await patient_service.create_profile(user.userId, base_payload)