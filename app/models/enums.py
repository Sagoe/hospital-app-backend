"""
Enum definitions shared across ORM models, Pydantic schemas, and
(mirrored) TypeScript types on the frontend. Kept in one module so the
Postgres ENUM types, Python enums, and generated TS types never drift.
"""

import enum


class UserRole(str, enum.Enum):
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    NURSE = "NURSE"
    ADMIN = "ADMIN"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    UNDISCLOSED = "UNDISCLOSED"


class BloodType(str, enum.Enum):
    A_POS = "A+"
    A_NEG = "A-"
    B_POS = "B+"
    B_NEG = "B-"
    AB_POS = "AB+"
    AB_NEG = "AB-"
    O_POS = "O+"
    O_NEG = "O-"


class AvailabilityStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ON_LEAVE = "ON_LEAVE"
    IN_SURGERY = "IN_SURGERY"


class AppointmentType(str, enum.Enum):
    IN_PERSON = "IN_PERSON"
    TELEHEALTH = "TELEHEALTH"
    FOLLOW_UP = "FOLLOW_UP"


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class AuditActionType(str, enum.Enum):
    READ_PHI = "READ_PHI"
    WRITE_PHI = "WRITE_PHI"
    AUTH_LOGIN = "AUTH_LOGIN"
    DATA_EXPORT = "DATA_EXPORT"
