"""Audit Log repository — append-only. No update/delete methods exist
here on purpose; the compliance log must never be mutated after write."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.enums import AuditActionType


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        performed_by_user_id: uuid.UUID | None,
        action_type: AuditActionType,
        target_record_id: uuid.UUID,
        target_table: str,
        ip_address: str,
    ) -> AuditLog:
        log = AuditLog(
            performedByUserId=performed_by_user_id,
            actionType=action_type,
            targetRecordId=target_record_id,
            targetTable=target_table,
            ipAddress=ip_address,
        )
        self._session.add(log)
        await self._session.flush()
        await self._session.refresh(log)
        return log

    async def list_by_target_record(self, target_record_id: uuid.UUID) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLog)
            .where(AuditLog.targetRecordId == target_record_id)
            .order_by(AuditLog.timestamp.desc())
        )
        return list(result.scalars().all())

    async def list_by_user(self, performed_by_user_id: uuid.UUID) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLog)
            .where(AuditLog.performedByUserId == performed_by_user_id)
            .order_by(AuditLog.timestamp.desc())
        )
        return list(result.scalars().all())
