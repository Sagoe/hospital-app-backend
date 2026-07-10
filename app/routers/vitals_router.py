"""Vitals router — nurses record vitals for their assigned patients;
doctors and admins read them for clinical review."""

import uuid

from fastapi import APIRouter, Depends, Request, status

from app.core.dependencies import CurrentUser, get_client_ip, get_vitals_service, require_role
from app.models.enums import UserRole
from app.schemas.vitals import VitalSignsCreate, VitalSignsRead
from app.services.vitals_service import VitalsService

router = APIRouter(prefix="/api/v1/vitals", tags=["vitals"])


@router.post(
    "",
    response_model=VitalSignsRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.NURSE))],
)
async def record_vitals(
    payload: VitalSignsCreate,
    request: Request,
    current_user: CurrentUser,
    vitals_service: VitalsService = Depends(get_vitals_service),
) -> VitalSignsRead:
    return await vitals_service.record_vitals(payload, current_user.userId, get_client_ip(request))


@router.get(
    "/patient/{patient_id}",
    response_model=list[VitalSignsRead],
    dependencies=[Depends(require_role(UserRole.DOCTOR, UserRole.NURSE, UserRole.ADMIN))],
)
async def list_vitals_for_patient(
    patient_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    vitals_service: VitalsService = Depends(get_vitals_service),
) -> list[VitalSignsRead]:
    return await vitals_service.list_for_patient(patient_id, current_user.userId, get_client_ip(request))