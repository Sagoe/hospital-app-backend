"""Appointment entity."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import AppointmentStatus, AppointmentType


class Appointment(Base):
    __tablename__ = "appointments"

    appointmentId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    patientId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_profiles.patientId", ondelete="CASCADE"), nullable=False
    )
    doctorId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctor_profiles.doctorId", ondelete="CASCADE"), nullable=False
    )
    startTime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    endTime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    appointmentType: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType, name="appointment_type"), nullable=False
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointment_status"),
        default=AppointmentStatus.SCHEDULED,
        nullable=False,
    )
    reasonForVisit: Mapped[str] = mapped_column(Text, nullable=False)
    # Dynamically generated Twilio Video room SID; populated only when
    # appointmentType == TELEHEALTH, by TelehealthService on confirmation.
    telehealthRoomId: Mapped[str | None] = mapped_column(String(100), nullable=True)

    patient: Mapped["PatientProfile"] = relationship(back_populates="appointments")
    doctor: Mapped["DoctorProfile"] = relationship(back_populates="appointments")
    encounter: Mapped["ClinicalEncounter | None"] = relationship(
        back_populates="appointment", uselist=False, cascade="all, delete-orphan"
    )
