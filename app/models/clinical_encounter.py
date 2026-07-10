"""Clinical Encounter & Medical Record entity.

`encryptedDiagnosisText` is ciphertext-only at rest (AES-256-GCM via
FieldEncryptionService). `prescriptionData` is stored as JSONB; each
array element is expected to carry medicationName, dosage,
refillsAllowed, and instructions, validated at the Pydantic schema
layer before it ever reaches this model.
"""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ClinicalEncounter(Base):
    __tablename__ = "clinical_encounters"

    encounterId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    appointmentId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.appointmentId", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    patientId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_profiles.patientId", ondelete="CASCADE"), nullable=False
    )
    doctorId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctor_profiles.doctorId", ondelete="CASCADE"), nullable=False
    )
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)
    clinicalNotes: Mapped[str] = mapped_column(Text, nullable=False)
    icd10Code: Mapped[str] = mapped_column(String(10), nullable=False)

    # List[{ medicationName, dosage, refillsAllowed, instructions }]
    prescriptionData: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)

    # Ciphertext (base64 AES-256-GCM payload).
    encryptedDiagnosisText: Mapped[str] = mapped_column(Text, nullable=False)

    appointment: Mapped["Appointment"] = relationship(back_populates="encounter")
    patient: Mapped["PatientProfile"] = relationship(back_populates="encounters")
    doctor: Mapped["DoctorProfile"] = relationship(back_populates="encounters")
    prescriptions: Mapped[list["Prescription"]] = relationship(back_populates="encounter")
