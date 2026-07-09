"""Doctor router — profile management and public-facing directory search."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import CurrentUser, get_doctor_service, require_role
from app.models.enums import UserRole
from app.schemas.doctor import DoctorProfileCreate, DoctorProfileRead, DoctorProfileUpdate
from app.services.doctor_service import DoctorNotFoundError, DoctorService

router = APIRouter(prefix="/api/v1/doctors", tags=["doctors"])


@router.post(
    "",
    response_model=DoctorProfileRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def create_doctor_profile(
    payload: DoctorProfileCreate,
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> DoctorProfileRead:
    # The target userId comes from the payload (the doctor/nurse account
    # being onboarded), not from the admin submitting this request.
    doctor = await doctor_service.create_profile(payload.userId, payload)
    return DoctorProfileRead.model_validate(doctor)


@router.get(
    "/me",
    response_model=DoctorProfileRead,
    dependencies=[Depends(require_role(UserRole.DOCTOR))],
)
async def get_my_doctor_profile(
    current_user: CurrentUser,
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> DoctorProfileRead:
    try:
        doctor = await doctor_service.get_profile_by_user_id(current_user.userId)
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DoctorProfileRead.model_validate(doctor)


@router.get("/search", response_model=list[DoctorProfileRead])
async def search_doctors(
    specialty: str | None = None,
    available_only: bool = False,
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> list[DoctorProfileRead]:
    if available_only:
        doctors = await doctor_service.list_available()
    elif specialty:
        doctors = await doctor_service.search_by_specialty(specialty)
    else:
        doctors = await doctor_service.list_available()
    return [DoctorProfileRead.model_validate(d) for d in doctors]


@router.get("/{doctor_id}", response_model=DoctorProfileRead)
async def get_doctor_profile(
    doctor_id: uuid.UUID,
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> DoctorProfileRead:
    try:
        doctor = await doctor_service.get_profile(doctor_id)
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DoctorProfileRead.model_validate(doctor)


@router.patch(
    "/{doctor_id}",
    response_model=DoctorProfileRead,
    dependencies=[Depends(require_role(UserRole.DOCTOR, UserRole.ADMIN))],
)
async def update_doctor_profile(
    doctor_id: uuid.UUID,
    payload: DoctorProfileUpdate,
    doctor_service: DoctorService = Depends(get_doctor_service),
) -> DoctorProfileRead:
    try:
        doctor = await doctor_service.update_profile(doctor_id, payload)
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return DoctorProfileRead.model_validate(doctor)