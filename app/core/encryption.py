"""
Field-level encryption service.

Every model attribute prefixed with `encrypted` (e.g. `encryptedNationalId`,
`encryptedDiagnosisText`) MUST pass through this service before being
persisted, and MUST be decrypted through this service when read back out
for an authorized caller. Ciphertext is never handled directly by
repositories, services, or routers.

Algorithm: AES-256-GCM (authenticated encryption).
Storage format: base64( nonce(12 bytes) || ciphertext || tag(16 bytes) )
This keeps a single opaque string per column, which maps cleanly onto a
SQLAlchemy `String`/`Text` column with no schema changes required if the
encryption scheme is later rotated.
"""

import base64
import os
from functools import lru_cache

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings, get_settings


class EncryptionError(Exception):
    """Raised when encryption or decryption of a PHI field fails."""


class FieldEncryptionService:
    """
    Stateless AES-256-GCM encrypt/decrypt helper for a single symmetric key.

    A new random 96-bit nonce is generated for every encryption call.
    GCM is a stream construction, so nonce reuse under the same key is
    catastrophic (it leaks the authentication key) — never cache or
    hardcode nonces.
    """

    NONCE_SIZE_BYTES = 12  # 96 bits, the NIST-recommended size for GCM

    def __init__(self, base64_key: str) -> None:
        try:
            key_bytes = base64.urlsafe_b64decode(base64_key.encode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - we re-wrap regardless of cause
            raise EncryptionError(
                "DATA_ENCRYPTION_KEY is not valid URL-safe base64."
            ) from exc

        if len(key_bytes) != 32:
            raise EncryptionError(
                "DATA_ENCRYPTION_KEY must decode to exactly 32 bytes for AES-256."
            )

        self._aesgcm = AESGCM(key_bytes)

    def encrypt(self, plaintext: str | None) -> str | None:
        """Encrypt a plaintext string. Passes through None unchanged so
        nullable PHI fields (e.g. optional insurance identifiers) don't
        force encryption of empty data."""
        if plaintext is None:
            return None

        nonce = os.urandom(self.NONCE_SIZE_BYTES)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        payload = nonce + ciphertext
        return base64.b64encode(payload).decode("utf-8")

    def decrypt(self, encoded_payload: str | None) -> str | None:
        """Decrypt a value produced by `encrypt`. Raises EncryptionError on
        tampering, wrong key, or malformed payload rather than returning
        corrupted PHI silently."""
        if encoded_payload is None:
            return None

        try:
            raw = base64.b64decode(encoded_payload.encode("utf-8"))
            nonce, ciphertext = raw[: self.NONCE_SIZE_BYTES], raw[self.NONCE_SIZE_BYTES :]
            plaintext_bytes = self._aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext_bytes.decode("utf-8")
        except InvalidTag as exc:
            raise EncryptionError(
                "PHI field failed integrity verification (tampering or wrong key)."
            ) from exc
        except Exception as exc:  # noqa: BLE001
            raise EncryptionError("Failed to decrypt PHI field.") from exc


@lru_cache
def get_encryption_service(settings: Settings | None = None) -> FieldEncryptionService:
    """Cached singleton so the AESGCM context isn't rebuilt per-request."""
    settings = settings or get_settings()
    return FieldEncryptionService(base64_key=settings.DATA_ENCRYPTION_KEY)
