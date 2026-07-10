from app.routers.admin_router import router as admin_router
from app.routers.appointment_router import router as appointment_router
from app.routers.audit_router import router as audit_router
from app.routers.auth_router import router as auth_router
from app.routers.clinical_encounter_router import router as encounter_router
from app.routers.doctor_router import router as doctor_router
from app.routers.patient_router import router as patient_router
from app.routers.prescription_router import router as prescription_router
from app.routers.reception_router import router as reception_router
from app.routers.vitals_router import router as vitals_router

all_routers = [
    auth_router,
    admin_router,
    patient_router,
    doctor_router,
    appointment_router,
    encounter_router,
    prescription_router,
    reception_router,
    vitals_router,
    audit_router,
]