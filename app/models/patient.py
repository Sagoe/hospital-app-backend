"""Patient Profile entity. `encryptedNationalId` is stored ciphertext-only;
plaintext never touches this model — see app.core.encryption and
app.repositories.patient_repository for the encrypt/decrypt boundary."""

import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import BloodType, Gender


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    patientId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    userId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.userId", ondelete="CASCADE"), nullable=False, unique=True
    )
    firstName: Mapped[str] = mapped_column(String(100), nullable=False)
    lastName: Mapped[str] = mapped_column(String(100), nullable=False)
    dateOfBirth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, name="gender"), nullable=False)
    phoneNumber: Mapped[str] = mapped_column(String(20), nullable=False)
    emergencyContactName: Mapped[str] = mapped_column(String(150), nullable=False)
    emergencyContactPhone: Mapped[str] = mapped_column(String(20), nullable=False)
    bloodType: Mapped[BloodType] = mapped_column(Enum(BloodType, name="blood_type"), nullable=False)

    # Ciphertext (base64 AES-256-GCM payload) — see FieldEncryptionService.
    encryptedNationalId: Mapped[str] = mapped_column(String(512), nullable=False)

    insuranceProvider: Mapped[str | None] = mapped_column(String(150), nullable=True)
    insurancePolicyNumber: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user: Mapped["User"] = relationship(back_populates="patient_profile")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="patient")
    encounters: Mapped[list["ClinicalEncounter"]] = relationship(back_populates="patient")
