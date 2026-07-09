"""Admin router — staff account provisioning.

Only an authenticated ADMIN may create DOCTOR/NURSE/ADMIN accounts.
Patients self-register via /auth/register; that endpoint rejects
non-PATIENT roles, so this is the only path to create staff accounts.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_auth_service, require_role
from app.models.enums import UserRole
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthError, AuthService

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@router.post("/staff", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_staff_account(
    payload: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    try:
        user = await auth_service.register_staff(payload)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserRead.model_validate(user)