"""Prescription entity — one row per medicine line item, created
alongside a ClinicalEncounter. This is the source of truth for the
pharmacy workflow (fulfillment status, per-patient/per-pharmacist
querying); ClinicalEncounter.prescriptionData remains the doctor-facing
JSONB summary shown inline on the encounter record and is left
untouched by this addition."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import PrescriptionStatus


class Prescription(Base):
    __tablename__ = "prescriptions"

    prescriptionId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    encounterId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinical_encounters.encounterId", ondelete="CASCADE"), nullable=False
    )
    patientId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_profiles.patientId", ondelete="CASCADE"), nullable=False
    )
    doctorId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctor_profiles.doctorId", ondelete="CASCADE"), nullable=False
    )

    medicationName: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    durationDays: Mapped[int] = mapped_column(Integer, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[PrescriptionStatus] = mapped_column(
        Enum(PrescriptionStatus, name="prescription_status"),
        default=PrescriptionStatus.PENDING,
        nullable=False,
    )
    fulfilledByUserId: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.userId", ondelete="SET NULL"), nullable=True
    )
    fulfilledAt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    prescribedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    encounter: Mapped["ClinicalEncounter"] = relationship(back_populates="prescriptions")
    patient: Mapped["PatientProfile"] = relationship(back_populates="prescriptions")
    doctor: Mapped["DoctorProfile"] = relationship()