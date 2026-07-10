"""Reception router — front-desk patient intake.

Creates the patient's User account and PatientProfile in a single
step, bypassing the self-service-only rule on POST /api/v1/patients
(which requires the caller to already be the patient in question).
Also exposes a nurse directory so reception can pick who to assign a
newly created patient to.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_auth_service, get_patient_service, get_user_repository, require_role
from app.models.enums import UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.patient import PatientProfileCreate, PatientProfileRead
from app.schemas.reception import PatientIntakeCreate
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthError, AuthService
from app.services.patient_service import PatientService

router = APIRouter(
    prefix="/api/v1/reception",
    tags=["reception"],
    dependencies=[Depends(require_role(UserRole.RECEPTIONIST, UserRole.ADMIN))],
)


@router.post("/patients", response_model=PatientProfileRead, status_code=status.HTTP_201_CREATED)
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

    profile_payload = PatientProfileCreate(
        firstName=payload.firstName,
        lastName=payload.lastName,
        dateOfBirth=payload.dateOfBirth,
        gender=payload.gender,
        phoneNumber=payload.phoneNumber,
        emergencyContactName=payload.emergencyContactName,
        emergencyContactPhone=payload.emergencyContactPhone,
        bloodType=payload.bloodType,
        nationalId=payload.nationalId,
        insuranceProvider=payload.insuranceProvider,
        insurancePolicyNumber=payload.insurancePolicyNumber,
    )
    return await patient_service.create_profile(user.userId, profile_payload)


@router.get("/nurses", response_model=list[UserRead])
async def list_nurses(
    user_repository: UserRepository = Depends(get_user_repository),
) -> list[UserRead]:
    nurses = await user_repository.list_by_role(UserRole.NURSE)
    return [UserRead.model_validate(n) for n in nurses]