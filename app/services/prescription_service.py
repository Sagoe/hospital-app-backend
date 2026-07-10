"""Prescription service — pharmacy fulfillment workflow."""

import uuid

from app.models.enums import AuditActionType
from app.repositories.prescription_repository import PrescriptionRepository
from app.schemas.prescription import PrescriptionRead
from app.services.audit_service import AuditService


class PrescriptionNotFoundError(Exception):
    pass


class PrescriptionService:
    def __init__(
        self, prescription_repository: PrescriptionRepository, audit_service: AuditService
    ) -> None:
        self._prescription_repository = prescription_repository
        self._audit_service = audit_service

    async def list_pending(self) -> list[PrescriptionRead]:
        prescriptions = await self._prescription_repository.list_pending()
        return [PrescriptionRead.model_validate(p) for p in prescriptions]

    async def list_for_patient(
        self, patient_id: uuid.UUID, requesting_user_id: uuid.UUID, ip_address: str
    ) -> list[PrescriptionRead]:
        prescriptions = await self._prescription_repository.list_by_patient(patient_id)

        await self._audit_service.record(
            performed_by_user_id=requesting_user_id,
            action_type=AuditActionType.READ_PHI,
            target_record_id=patient_id,
            target_table="prescriptions",
            ip_address=ip_address,
        )

        return [PrescriptionRead.model_validate(p) for p in prescriptions]

    async def fulfill(
        self, prescription_id: uuid.UUID, pharmacist_user_id: uuid.UUID, ip_address: str
    ) -> PrescriptionRead:
        prescription = await self._prescription_repository.get_by_id(prescription_id)
        if prescription is None:
            raise PrescriptionNotFoundError(f"Prescription {prescription_id} not found.")

        updated = await self._prescription_repository.fulfill(prescription, pharmacist_user_id)

        await self._audit_service.record(
            performed_by_user_id=pharmacist_user_id,
            action_type=AuditActionType.WRITE_PHI,
            target_record_id=updated.prescriptionId,
            target_table="prescriptions",
            ip_address=ip_address,
        )

        return PrescriptionRead.model_validate(updated)