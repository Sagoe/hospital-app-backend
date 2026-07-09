"""
Central dependency wiring.

Routers depend only on functions in this module (never directly on
repositories or the raw DB session), which keeps the Controller layer
thin and makes it trivial to override dependencies in tests.
"""

import uuid
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import FieldEncryptionService, get_encryption_service
from app.core.security import TokenError, decode_access_token
from app.db.session import get_db_session
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.doctor_repository import DoctorRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.user_repository import UserRepository
from app.repositories.clinical_encounter_repository import ClinicalEncounterRepository
from app.services.appointment_service import AppointmentService
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService
from app.services.clinical_encounter_service import ClinicalEncounterService
from app.services.doctor_service import DoctorService
from app.services.patient_service import PatientService
from app.services.telehealth_service import TelehealthService

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# --- Repositories ---

def get_user_repository(session: DbSession) -> UserRepository:
    return UserRepository(session)


def get_patient_repository(session: DbSession) -> PatientRepository:
    return PatientRepository(session)


def get_doctor_repository(session: DbSession) -> DoctorRepository:
    return DoctorRepository(session)


def get_appointment_repository(session: DbSession) -> AppointmentRepository:
    return AppointmentRepository(session)


def get_encounter_repository(session: DbSession) -> ClinicalEncounterRepository:
    return ClinicalEncounterRepository(session)


def get_audit_log_repository(session: DbSession) -> AuditLogRepository:
    return AuditLogRepository(session)


# --- Cross-cutting services ---

def get_audit_service(
    audit_repository: Annotated[AuditLogRepository, Depends(get_audit_log_repository)],
) -> AuditService:
    return AuditService(audit_repository)


def get_encryption_service_dep() -> FieldEncryptionService:
    return get_encryption_service()


def get_telehealth_service() -> TelehealthService:
    return TelehealthService()


# --- Domain services ---

def get_auth_service(
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> AuthService:
    return AuthService(user_repository, audit_service)


def get_patient_service(
    patient_repository: Annotated[PatientRepository, Depends(get_patient_repository)],
    encryption_service: Annotated[FieldEncryptionService, Depends(get_encryption_service_dep)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> PatientService:
    return PatientService(patient_repository, encryption_service, audit_service)


def get_doctor_service(
    doctor_repository: Annotated[DoctorRepository, Depends(get_doctor_repository)],
) -> DoctorService:
    return DoctorService(doctor_repository)


def get_appointment_service(
    appointment_repository: Annotated[AppointmentRepository, Depends(get_appointment_repository)],
    telehealth_service: Annotated[TelehealthService, Depends(get_telehealth_service)],
) -> AppointmentService:
    return AppointmentService(appointment_repository, telehealth_service)


def get_encounter_service(
    encounter_repository: Annotated[ClinicalEncounterRepository, Depends(get_encounter_repository)],
    encryption_service: Annotated[FieldEncryptionService, Depends(get_encryption_service_dep)],
    audit_service: Annotated[AuditService, Depends(get_audit_service)],
) -> ClinicalEncounterService:
    return ClinicalEncounterService(encounter_repository, encryption_service, audit_service)


# --- Auth guards ---

async def get_current_user(
    token: Annotated[str, Depends(_oauth2_scheme)],
    user_repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> User:
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id_raw = payload.get("sub")
    try:
        user_id = uuid.UUID(user_id_raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await user_repository.get_by_id(user_id)
    if user is None or not user.isActive:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*allowed_roles: UserRole) -> Callable[[CurrentUser], User]:
    """Route-level guard factory: `Depends(require_role(UserRole.ADMIN))`."""

    def _check(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _check
