"""VitalSigns entity — recorded by a nurse for an assigned patient and
surfaced to that patient's assigned doctor."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class VitalSigns(Base):
    __tablename__ = "vital_signs"

    vitalId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patientId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_profiles.patientId", ondelete="CASCADE"), nullable=False
    )
    nurseId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.userId", ondelete="SET NULL"), nullable=True
    )

    bloodPressureSystolic: Mapped[int] = mapped_column(Integer, nullable=False)
    bloodPressureDiastolic: Mapped[int] = mapped_column(Integer, nullable=False)
    heartRate: Mapped[int] = mapped_column(Integer, nullable=False)
    temperatureCelsius: Mapped[float] = mapped_column(Numeric(4, 1), nullable=False)
    respiratoryRate: Mapped[int] = mapped_column(Integer, nullable=False)
    oxygenSaturation: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    recordedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    patient: Mapped["PatientProfile"] = relationship(back_populates="vital_signs")
    nurse: Mapped["User"] = relationship()