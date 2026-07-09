"""
Telehealth service — wraps Twilio Video room provisioning.

Rooms are created lazily, only when an appointment of type TELEHEALTH
is confirmed, and are named deterministically from the appointmentId so
a retried request can't create duplicate rooms for the same appointment.
"""

import uuid

from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from app.core.config import Settings, get_settings


class TelehealthProvisioningError(Exception):
    pass


class TelehealthService:
    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        self._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    async def create_video_room(self, appointment_id: uuid.UUID) -> str:
        """
        Creates (or idempotently fetches) a Twilio Video "group" room for
        the given appointment and returns its SID for storage in
        `telehealthRoomId`.

        The Twilio Python SDK is synchronous; in a real deployment this
        call should be dispatched via `anyio.to_thread.run_sync` from the
        calling async service so it doesn't block the event loop. That
        wrapping is done by the caller (AppointmentService) to keep this
        class a thin, directly-testable Twilio adapter.
        """
        import anyio

        room_unique_name = f"appointment-{appointment_id}"
        return await anyio.to_thread.run_sync(self._create_or_fetch_room_sync, room_unique_name, appointment_id)

    def _create_or_fetch_room_sync(self, room_unique_name: str, appointment_id: uuid.UUID) -> str:
        try:
            room = self._client.video.v1.rooms.create(
                unique_name=room_unique_name,
                type="group",
                record_participants_on_connect=False,
            )
            return room.sid
        except TwilioRestException as exc:
            if exc.status == 400 and "already exists" in (exc.msg or "").lower():
                existing = self._client.video.v1.rooms(room_unique_name).fetch()
                return existing.sid
            raise TelehealthProvisioningError(
                f"Failed to provision Twilio video room for appointment {appointment_id}."
            ) from exc
