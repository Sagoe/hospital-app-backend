"""
Audit service — the single place that writes to the compliance log.

Other services call `record` directly after a PHI read/write or auth
event; routers do not call the repository directly, so no endpoint can
forget to audit a PHI access path.
"""

import uuid

from app.models.enums import AuditActionType
from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, audit_repository: AuditLogRepository) -> None:
        self._audit_repository = audit_repository

    async def record(
        self,
        *,
        performed_by_user_id: uuid.UUID | None,
        action_type: AuditActionType,
        target_record_id: uuid.UUID,
        target_table: str,
        ip_address: str,
    ) -> None:
        await self._audit_repository.create(
            performed_by_user_id=performed_by_user_id,
            action_type=action_type,
            target_record_id=target_record_id,
            target_table=target_table,
            ip_address=ip_address,
        )
