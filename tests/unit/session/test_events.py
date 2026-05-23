"""Tests for session events and protocol serialization."""

import json

from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType
from fluentia.session.protocol import PROTOCOL_VERSION
from fluentia.session.protocol import deserialize_client_message
from fluentia.session.protocol import serialize_event


class TestSessionEvent:
    def test_event_creation(self):
        event = SessionEvent(type=SessionEventType.TURN_COMPLETE)
        assert event.type == SessionEventType.TURN_COMPLETE
        assert event.payload == {}

    def test_event_with_payload(self):
        event = SessionEvent(
            type=SessionEventType.AUDIO, payload={"data": "base64...", "sample_rate": 24000}
        )
        assert event.payload["sample_rate"] == 24000


class TestProtocol:
    def test_serialize_includes_version(self):
        event = SessionEvent(type=SessionEventType.TURN_COMPLETE)
        raw = serialize_event(event)
        msg = json.loads(raw)
        assert msg["v"] == PROTOCOL_VERSION
        assert msg["type"] == "turn_complete"

    def test_serialize_includes_timestamp(self):
        event = SessionEvent(type=SessionEventType.TURN_COMPLETE)
        raw = serialize_event(event)
        msg = json.loads(raw)
        assert "ts" in msg

    def test_serialize_payload(self):
        event = SessionEvent(
            type=SessionEventType.ERROR, payload={"message": "test error", "recoverable": False}
        )
        raw = serialize_event(event)
        msg = json.loads(raw)
        assert msg["payload"]["message"] == "test error"

    def test_deserialize_client_message(self):
        raw = json.dumps({"type": "text", "text": "hello"})
        msg = deserialize_client_message(raw)
        assert msg["type"] == "text"
        assert msg["text"] == "hello"
