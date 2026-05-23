"""WebSocket message serialization and protocol versioning."""

import json
from datetime import UTC
from datetime import datetime
from typing import Any

from fluentia.session.events import SessionEvent

PROTOCOL_VERSION: int = 1


def serialize_event(event: SessionEvent) -> str:
    """Serialize a SessionEvent to a JSON string for WebSocket transmission.

    Every server-to-client message includes the protocol version.
    """
    message: dict[str, Any] = {
        "v": PROTOCOL_VERSION,
        "type": event.type.value,
        "payload": event.payload,
        "ts": datetime.now(tz=UTC).isoformat(),
    }
    return json.dumps(message)


def deserialize_client_message(raw: str) -> dict[str, Any]:
    """Deserialize a client-to-server text message."""
    result: dict[str, Any] = json.loads(raw)
    return result
