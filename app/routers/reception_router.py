"""Reception router — front-desk patient intake.

Creates the patient's User account and PatientProfile in a single
step, bypassing the self-service-only rule on POST /api/v1/patients
(which requires the caller to already be the patient in question).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_auth_service, get_patient_service, require_role
from app.models.enums import UserRole
from app.schemas.patient import PatientProfileCreate, PatientProfileRead
from app.schemas.reception import PatientIntakeCreate
from app.schemas.user import UserCreate
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