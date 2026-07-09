"""Auth router: registration, login, and MFA enrollment/verification."""

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import CurrentUser, get_auth_service, get_client_ip
from app.schemas.user import (
    MfaEnrollResponse,
    MfaVerifyRequest,
    TokenResponse,
    UserCreate,
    UserLoginRequest,
    UserRead,
)
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    try:
        user = await auth_service.register(payload)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return await auth_service.login(payload, ip_address=get_client_ip(request))
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/mfa/enroll", response_model=MfaEnrollResponse)
async def enroll_mfa(
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
) -> MfaEnrollResponse:
    return await auth_service.enroll_mfa(current_user)


@router.post("/mfa/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_mfa(
    payload: MfaVerifyRequest,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    try:
        await auth_service.verify_and_enable_mfa(current_user, payload.mfaCode)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
