"""Doctor / Medical Staff entity."""

import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import AvailabilityStatus


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    doctorId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    userId: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.userId", ondelete="CASCADE"), nullable=False, unique=True
    )
    specialty: Mapped[str] = mapped_column(String(150), nullable=False)
    licenseNumber: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    departmentId: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    consultationFee: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    availabilityStatus: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus, name="availability_status"),
        default=AvailabilityStatus.AVAILABLE,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="doctor_profile")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="doctor")
    encounters: Mapped[list["ClinicalEncounter"]] = relationship(back_populates="doctor")
