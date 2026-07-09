"""Audit Log router — read-only, ADMIN-only. There is intentionally no
create/update/delete endpoint; logs are written internally by services."""

import uuid

from fastapi import APIRouter, Depends

from app.core.dependencies import get_audit_log_repository, require_role
from app.models.enums import UserRole
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogRead

router = APIRouter(
    prefix="/api/v1/audit-logs",
    tags=["audit"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@router.get("/record/{target_record_id}", response_model=list[AuditLogRead])
async def get_logs_for_record(
    target_record_id: uuid.UUID,
    audit_repository: AuditLogRepository = Depends(get_audit_log_repository),
) -> list[AuditLogRead]:
    logs = await audit_repository.list_by_target_record(target_record_id)
    return [AuditLogRead.model_validate(log) for log in logs]


@router.get("/user/{user_id}", response_model=list[AuditLogRead])
async def get_logs_for_user(
    user_id: uuid.UUID,
    audit_repository: AuditLogRepository = Depends(get_audit_log_repository),
) -> list[AuditLogRead]:
    logs = await audit_repository.list_by_user(user_id)
    return [AuditLogRead.model_validate(log) for log in logs]
