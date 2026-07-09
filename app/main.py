"""
FastAPI application entrypoint.

Run with: uvicorn app.main:app --reload --port ${PORT}
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.encryption import EncryptionError
from app.routers import all_routers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hospital_app")

settings = get_settings()

app = FastAPI(
    title="Hospital Web Application API",
    version="1.0.0",
    description=(
        "Enterprise-grade Hospital Web Application backend serving the "
        "Patient, Doctor/Medical Staff, and Admin portals."
    ),
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["https://medicare-frontend.vercel.app"]
        if settings.is_production
        else ["http://localhost:3000"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in all_routers:
    app.include_router(router)


@app.exception_handler(EncryptionError)
async def encryption_error_handler(request: Request, exc: EncryptionError) -> JSONResponse:
    logger.error("PHI encryption/decryption failure: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "A data integrity error occurred while processing protected health information."},
    )


@app.get("/api/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.NODE_ENV}