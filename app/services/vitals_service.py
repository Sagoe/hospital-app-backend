"""Vital signs service. Vitals are clinical/PHI-adjacent data; reads and
writes are audited the same way as PatientService/ClinicalEncounterService."""

import uuid

from app.models.enums import AuditActionType
from app.repositories.vitals_repository import VitalsRepository
from app.schemas.vitals import VitalSignsCreate, VitalSignsRead
from app.services.audit_service import AuditService


class VitalsService:
    def __init__(self, vitals_repository: VitalsRepository, audit_service: AuditService) -> None:
        self._vitals_repository = vitals_repository
        self._audit_service = audit_service

    async def record_vitals(
        self, payload: VitalSignsCreate, nurse_user_id: uuid.UUID, ip_address: str
    ) -> VitalSignsRead:
        vital = await self._vitals_repository.create(
            patient_id=payload.patientId,
            nurse_id=nurse_user_id,
            blood_pressure_systolic=payload.bloodPressureSystolic,
            blood_pressure_diastolic=payload.bloodPressureDiastolic,
            heart_rate=payload.heartRate,
            temperature_celsius=payload.temperatureCelsius,
            respiratory_rate=payload.respiratoryRate,
            oxygen_saturation=payload.oxygenSaturation,
            notes=payload.notes,
        )

        await self._audit_service.record(
            performed_by_user_id=nurse_user_id,
            action_type=AuditActionType.WRITE_PHI,
            target_record_id=vital.vitalId,
            target_table="vital_signs",
            ip_address=ip_address,
        )

        return VitalSignsRead.model_validate(vital)

    async def list_for_patient(
        self, patient_id: uuid.UUID, requesting_user_id: uuid.UUID, ip_address: str
    ) -> list[VitalSignsRead]:
        vitals = await self._vitals_repository.list_by_patient(patient_id)

        await self._audit_service.record(
            performed_by_user_id=requesting_user_id,
            action_type=AuditActionType.READ_PHI,
            target_record_id=patient_id,
            target_table="vital_signs",
            ip_address=ip_address,
        )

        return [VitalSignsRead.model_validate(v) for v in vitals]