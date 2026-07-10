"""Prescription router — pharmacy queue and fulfillment."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.dependencies import CurrentUser, get_client_ip, get_prescription_service, require_role
from app.models.enums import UserRole
from app.schemas.prescription import PrescriptionRead
from app.services.prescription_service import PrescriptionNotFoundError, PrescriptionService

router = APIRouter(prefix="/api/v1/prescriptions", tags=["prescriptions"])


@router.get(
    "/pending",
    response_model=list[PrescriptionRead],
    dependencies=[Depends(require_role(UserRole.PHARMACIST, UserRole.ADMIN))],
)
async def list_pending_prescriptions(
    prescription_service: PrescriptionService = Depends(get_prescription_service),
) -> list[PrescriptionRead]:
    return await prescription_service.list_pending()


@router.get(
    "/patient/{patient_id}",
    response_model=list[PrescriptionRead],
    dependencies=[Depends(require_role(UserRole.PHARMACIST, UserRole.DOCTOR, UserRole.ADMIN))],
)
async def list_prescriptions_for_patient(
    patient_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    prescription_service: PrescriptionService = Depends(get_prescription_service),
) -> list[PrescriptionRead]:
    return await prescription_service.list_for_patient(
        patient_id, current_user.userId, get_client_ip(request)
    )


@router.patch(
    "/{prescription_id}/fulfill",
    response_model=PrescriptionRead,
    dependencies=[Depends(require_role(UserRole.PHARMACIST))],
)
async def fulfill_prescription(
    prescription_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    prescription_service: PrescriptionService = Depends(get_prescription_service),
) -> PrescriptionRead:
    try:
        return await prescription_service.fulfill(
            prescription_id, current_user.userId, get_client_ip(request)
        )
    except PrescriptionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc