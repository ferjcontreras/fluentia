"""Base provider ABC and SessionContext."""

import abc
from collections.abc import Awaitable
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import WebSocket

from fluentia.agents.base import AgentDefinition
from fluentia.session.events import SessionEvent


@dataclass(frozen=True)
class SessionContext:
    """Shared context passed to a provider during a voice session."""

    user_id: str
    session_id: str
    agent_definition: AgentDefinition
    emit: Callable[[SessionEvent], Awaitable[None]]


class BaseProvider(abc.ABC):
    """Abstract base class for voice conversation providers."""

    @abc.abstractmethod
    async def handle_session(self, websocket: WebSocket, session_context: SessionContext) -> None:
        """Run a complete voice session over the given WebSocket.

        The provider:
        1. Connects to its external service using the agent definition's prompt
        2. Streams audio from the WebSocket to the external service
        3. Receives audio/text/events from the external service
        4. Emits normalized SessionEvents via session_context.emit()
        5. Handles tool calls if the agent definition includes tools
        6. Cleans up on disconnect or error
        """
        raise NotImplementedError("Subclasses must implement `handle_session()`")
