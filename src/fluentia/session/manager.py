"""Session manager: WebSocket session orchestration."""

import asyncio
import json
import logging
import time
from typing import Any

import structlog
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from fluentia.agents.base import AgentDefinition
from fluentia.agents.registry import AgentRegistry
from fluentia.observability.metrics import MetricsCollector
from fluentia.providers.base import BaseProvider
from fluentia.providers.base import SessionContext
from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType
from fluentia.session.protocol import serialize_event

logger: logging.Logger = logging.getLogger(__name__)


class SessionManager:
    """Orchestrates WebSocket voice sessions."""

    def __init__(
        self,
        providers: dict[str, BaseProvider],
        agent_registry: AgentRegistry,
        metrics: MetricsCollector,
        default_agent: str = "english_teacher",
    ) -> None:
        """Initialize the session manager."""
        self._providers: dict[str, BaseProvider] = providers
        self._agent_registry: AgentRegistry = agent_registry
        self._metrics: MetricsCollector = metrics
        self._default_agent: str = default_agent

    async def handle_websocket(
        self, websocket: WebSocket, provider_name: str, user_id: str, session_id: str
    ) -> None:
        """Handle a WebSocket voice session."""
        await websocket.accept()

        # Bind structured logging context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            session_id=session_id, user_id=user_id, provider=provider_name
        )

        # Resolve provider
        provider: BaseProvider | None = self._providers.get(provider_name)
        if provider is None:
            logger.error("Unknown provider: %s", provider_name)
            await websocket.close(code=1008, reason=f"Unknown provider: {provider_name}")
            return

        # Resolve agent from query params
        agent_name: str = websocket.query_params.get("agent", self._default_agent)

        # Resolve agent definition (before prompt_config so we can filter variables)
        try:
            agent_def: AgentDefinition = self._agent_registry.get(agent_name)
        except KeyError:
            logger.error("Unknown agent: %s", agent_name)
            await websocket.close(code=1008, reason=f"Unknown agent: {agent_name}")
            return

        # Wait for prompt_config message
        prompt_vars: dict[str, Any]
        enabled_tools: list[str] | None
        prompt_vars, enabled_tools = await self._receive_prompt_config(websocket, agent_def)

        # Apply prompt_config variables and tool overrides to agent definition
        if prompt_vars or enabled_tools is not None:
            agent_def = AgentDefinition(
                name=agent_def.name,
                display_name=agent_def.display_name,
                description=agent_def.description,
                template_path=agent_def.template_path,
                default_variables={**agent_def.default_variables, **prompt_vars},
                enabled_tools=enabled_tools
                if enabled_tools is not None
                else agent_def.enabled_tools,
                provider_settings=agent_def.provider_settings,
                field_metadata=agent_def.field_metadata,
            )

        structlog.contextvars.bind_contextvars(agent=agent_name)

        # Create emit callback that serializes and sends events over WebSocket
        async def emit(event: SessionEvent) -> None:
            try:
                await websocket.send_text(serialize_event(event))
            except (WebSocketDisconnect, RuntimeError):
                pass

        # Create session context
        context: SessionContext = SessionContext(
            user_id=user_id, session_id=session_id, agent_definition=agent_def, emit=emit
        )

        # Emit SESSION_START
        await emit(SessionEvent(type=SessionEventType.SESSION_START))
        self._metrics.session_started(provider=provider_name, agent=agent_name)
        start_time: float = time.monotonic()

        try:
            await provider.handle_session(websocket, context)
        except WebSocketDisconnect:
            logger.info("Client disconnected")
        except Exception:
            logger.exception("Session error")
            self._metrics.session_error(
                provider=provider_name, agent=agent_name, error_type="unhandled"
            )
        finally:
            duration: float = time.monotonic() - start_time
            self._metrics.session_ended(
                provider=provider_name, agent=agent_name, duration_seconds=round(duration, 2)
            )

            try:
                await emit(SessionEvent(type=SessionEventType.SESSION_END))
            except (WebSocketDisconnect, RuntimeError):
                pass

            logger.info("Session ended, duration=%.2fs", duration)

    async def _receive_prompt_config(
        self, websocket: WebSocket, agent_def: AgentDefinition
    ) -> tuple[dict[str, Any], list[str] | None]:
        """Read a prompt_config message from the WebSocket (5s timeout).

        Returns:
            A tuple of (variables dict, enabled_tools list or None).
        """
        try:
            raw: str = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
            data: dict[str, Any] = json.loads(raw)
            if data.get("type") != "prompt_config":
                return {}, None

            # Generic variables dict, filtered to keys the agent uses
            variables: dict[str, Any] = data.get("variables", {})
            known_keys: set[str] = set(agent_def.config_fields)
            result: dict[str, str] = {}
            for key, value in variables.items():
                if key in known_keys and isinstance(value, str) and value.strip():
                    result[key] = value

            # Extract tool overrides (None means use agent defaults)
            raw_tools: Any = data.get("enabled_tools")
            enabled_tools: list[str] | None = None
            if isinstance(raw_tools, list):
                enabled_tools = [t for t in raw_tools if isinstance(t, str)]

            logger.info("Received prompt_config with fields: %s", list(result.keys()))
            return result, enabled_tools

        except (TimeoutError, json.JSONDecodeError, Exception):
            logger.debug("No prompt_config received, using defaults")
            return {}, None
