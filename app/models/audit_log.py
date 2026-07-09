"""System Compliance Audit Log entity.

Rows are written by AuditService and are treated as append-only:
no repository method in this codebase exposes update or delete for
this table. Retention/purge, if ever required, must be a separate,
explicitly-authorized administrative operation outside normal app code paths.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import AuditActionType


class AuditLog(Base):
    __tablename__ = "audit_logs"

    logId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    performedByUserId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.userId", ondelete="SET NULL"), nullable=True
    )
    actionType: Mapped[AuditActionType] = mapped_column(
        Enum(AuditActionType, name="audit_action_type"), nullable=False
    )
    targetRecordId: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    targetTable: Mapped[str] = mapped_column(String(100), nullable=False)
    ipAddress: Mapped[str] = mapped_column(String(45), nullable=False)  # IPv6-safe length
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    performed_by: Mapped["User | None"] = relationship(back_populates="audit_logs")
