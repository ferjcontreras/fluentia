"""Normalized event types emitted by providers."""

from dataclasses import dataclass
from dataclasses import field
from enum import StrEnum
from typing import Any


class SessionEventType(StrEnum):
    """Normalized event types emitted by providers."""

    # Content delivery
    AUDIO = "audio"
    TEXT = "text"

    # Transcription
    INPUT_TRANSCRIPTION = "input_transcription"
    OUTPUT_TRANSCRIPTION = "output_transcription"

    # Session control
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    TURN_COMPLETE = "turn_complete"
    INTERRUPTED = "interrupted"

    # Tool lifecycle
    TOOL_STARTED = "tool_started"
    TOOL_PROGRESS = "tool_progress"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED = "tool_failed"

    # Errors
    ERROR = "error"


@dataclass(frozen=True)
class SessionEvent:
    """A normalized event emitted by a provider during a voice session."""

    type: SessionEventType
    payload: dict[str, Any] = field(default_factory=dict)
