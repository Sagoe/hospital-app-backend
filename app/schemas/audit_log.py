"""Pydantic schema for the (read-only, append-only) Audit Log entity."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AuditActionType


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    logId: uuid.UUID
    performedByUserId: uuid.UUID | None
    actionType: AuditActionType
    targetRecordId: uuid.UUID
    targetTable: str
    ipAddress: str
    timestamp: datetime
