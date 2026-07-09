"""
Import every model here so that `Base.metadata` is fully populated
before Alembic's `--autogenerate` (or `Base.metadata.create_all`)
inspects it. Alembic's env.py imports this module for that reason —
do not remove entries even if they look unused by static analysis.
"""

from app.db.session import Base
from app.models.appointment import Appointment  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.clinical_encounter import ClinicalEncounter  # noqa: F401
from app.models.doctor import DoctorProfile  # noqa: F401
from app.models.patient import PatientProfile  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    "Base",
    "User",
    "PatientProfile",
    "DoctorProfile",
    "Appointment",
    "ClinicalEncounter",
    "AuditLog",
]
