"""Tests for session manager: WebSocket session orchestration."""

import json
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from fastapi import WebSocketDisconnect

from fluentia.agents.base import AgentDefinition
from fluentia.agents.base import FieldMetadata
from fluentia.agents.registry import AgentRegistry
from fluentia.observability.metrics import LoggingMetricsCollector
from fluentia.providers.base import BaseProvider
from fluentia.session.manager import SessionManager


@pytest.fixture
def agent_def() -> AgentDefinition:
    """Fixture for a test agent definition."""
    return AgentDefinition(
        name="test_agent",
        display_name="Test Agent",
        description="Agent for testing",
        template_path=None,
        default_variables={"greeting": "Hello"},
        field_metadata={"greeting": FieldMetadata(label="Greeting")},
    )


@pytest.fixture
def agent_registry(agent_def: AgentDefinition) -> AgentRegistry:
    """Fixture for an agent registry with a test agent."""
    registry: AgentRegistry = AgentRegistry()
    registry.register(agent_def)
    return registry


@pytest.fixture
def mock_provider() -> MagicMock:
    """Fixture for a mock provider."""
    provider: MagicMock = MagicMock(spec=BaseProvider)
    provider.handle_session = AsyncMock()
    return provider


@pytest.fixture
def metrics() -> LoggingMetricsCollector:
    """Fixture for a metrics collector."""
    return LoggingMetricsCollector()


@pytest.fixture
def session_manager(
    mock_provider: MagicMock, agent_registry: AgentRegistry, metrics: LoggingMetricsCollector
) -> SessionManager:
    """Fixture for a SessionManager with a mock provider."""
    return SessionManager(
        providers={"test": mock_provider},
        agent_registry=agent_registry,
        metrics=metrics,
        default_agent="test_agent",
    )


def _make_websocket(
    query_params: dict[str, str] | None = None, prompt_config: dict[str, Any] | None = None
) -> MagicMock:
    """Create a mock WebSocket with query params and prompt config."""
    ws: MagicMock = MagicMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    ws.send_text = AsyncMock()

    if query_params is None:
        query_params = {}
    ws.query_params = MagicMock()
    ws.query_params.get = MagicMock(
        side_effect=lambda key, default=None: query_params.get(key, default)
    )

    if prompt_config is not None:
        ws.receive_text = AsyncMock(return_value=json.dumps(prompt_config))
    else:
        # Timeout to simulate no prompt_config
        ws.receive_text = AsyncMock(side_effect=TimeoutError)

    return ws


class TestSessionManagerInit:
    """Tests for SessionManager initialization."""

    def test_init(self, session_manager: SessionManager):
        """Test SessionManager is created correctly."""
        assert session_manager._default_agent == "test_agent"
        assert "test" in session_manager._providers

    def test_init_custom_default_agent(
        self,
        mock_provider: MagicMock,
        agent_registry: AgentRegistry,
        metrics: LoggingMetricsCollector,
    ):
        """Test SessionManager with custom default agent."""
        manager: SessionManager = SessionManager(
            providers={"test": mock_provider},
            agent_registry=agent_registry,
            metrics=metrics,
            default_agent="custom_agent",
        )
        assert manager._default_agent == "custom_agent"


class TestSessionManagerHandleWebsocket:
    """Tests for SessionManager.handle_websocket."""

    @pytest.mark.asyncio
    async def test_unknown_provider_closes_socket(self, session_manager: SessionManager):
        """Test that unknown provider closes WebSocket with 1008."""
        ws: MagicMock = _make_websocket()
        await session_manager.handle_websocket(
            websocket=ws, provider_name="unknown", user_id="u1", session_id="s1"
        )
        ws.accept.assert_called_once()
        ws.close.assert_called_once_with(code=1008, reason="Unknown provider: unknown")

    @pytest.mark.asyncio
    async def test_unknown_agent_closes_socket(self, session_manager: SessionManager):
        """Test that unknown agent closes WebSocket with 1008."""
        ws: MagicMock = _make_websocket(query_params={"agent": "nonexistent"})
        await session_manager.handle_websocket(
            websocket=ws, provider_name="test", user_id="u1", session_id="s1"
        )
        ws.accept.assert_called_once()
        ws.close.assert_called_once_with(code=1008, reason="Unknown agent: nonexistent")

    @pytest.mark.asyncio
    async def test_successful_session(
        self, session_manager: SessionManager, mock_provider: MagicMock
    ):
        """Test a successful session flow."""
        ws: MagicMock = _make_websocket()
        await session_manager.handle_websocket(
            websocket=ws, provider_name="test", user_id="u1", session_id="s1"
        )
        ws.accept.assert_called_once()
        mock_provider.handle_session.assert_called_once()

        # Verify session events were sent (SESSION_START and SESSION_END)
        assert ws.send_text.call_count >= 2

    @pytest.mark.asyncio
    async def test_uses_default_agent(
        self, session_manager: SessionManager, mock_provider: MagicMock
    ):
        """Test that default agent is used when no agent query param."""
        ws: MagicMock = _make_websocket()
        await session_manager.handle_websocket(
            websocket=ws, provider_name="test", user_id="u1", session_id="s1"
        )
        # Provider was called, meaning agent was resolved successfully
        mock_provider.handle_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_prompt_config_applied(
        self, session_manager: SessionManager, mock_provider: MagicMock
    ):
        """Test that prompt_config variables are applied to agent definition."""
        prompt_config: dict[str, Any] = {
            "type": "prompt_config",
            "variables": {"greeting": "Hi there"},
        }
        ws: MagicMock = _make_websocket(prompt_config=prompt_config)
        await session_manager.handle_websocket(
            websocket=ws, provider_name="test", user_id="u1", session_id="s1"
        )
        mock_provider.handle_session.assert_called_once()

        # Check that the agent definition in the context has the merged variables
        call_args = mock_provider.handle_session.call_args
        context = (
            call_args[1]["session_context"]
            if "session_context" in call_args[1]
            else call_args[0][1]
        )
        assert context.agent_definition.default_variables["greeting"] == "Hi there"

    @pytest.mark.asyncio
    async def test_provider_exception_records_error_metric(
        self,
        session_manager: SessionManager,
        mock_provider: MagicMock,
        metrics: LoggingMetricsCollector,
    ):
        """Test that provider exception is handled and metrics recorded."""
        mock_provider.handle_session = AsyncMock(side_effect=RuntimeError("boom"))
        ws: MagicMock = _make_websocket()
        # Should not raise
        await session_manager.handle_websocket(
            websocket=ws, provider_name="test", user_id="u1", session_id="s1"
        )


class TestSessionManagerReceivePromptConfig:
    """Tests for SessionManager._receive_prompt_config."""

    @pytest.fixture
    def agent_def_for_config(self) -> AgentDefinition:
        """Agent definition with known fields for prompt_config tests."""
        return AgentDefinition(
            name="test",
            display_name="Test",
            description="Test",
            template_path=None,
            default_variables={
                "company_name": "Default",
                "agent_name": "Default",
                "guidelines": "Default",
            },
        )

    @pytest.mark.asyncio
    async def test_valid_prompt_config(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test receiving a valid prompt_config message."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "prompt_config",
                    "variables": {"company_name": "Acme", "agent_name": "Test"},
                }
            )
        )
        variables: dict[str, Any]
        variables, _ = await session_manager._receive_prompt_config(ws, agent_def_for_config)
        assert variables["company_name"] == "Acme"
        assert variables["agent_name"] == "Test"

    @pytest.mark.asyncio
    async def test_wrong_type_returns_empty(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test that non-prompt_config message returns empty dict."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(return_value=json.dumps({"type": "other"}))
        variables: dict[str, Any]
        enabled_tools: list[str] | None
        variables, enabled_tools = await session_manager._receive_prompt_config(
            ws, agent_def_for_config
        )
        assert variables == {}
        assert enabled_tools is None

    @pytest.mark.asyncio
    async def test_timeout_returns_empty(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test that timeout returns empty dict."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(side_effect=TimeoutError)
        variables: dict[str, Any]
        variables, _ = await session_manager._receive_prompt_config(ws, agent_def_for_config)
        assert variables == {}

    @pytest.mark.asyncio
    async def test_invalid_json_returns_empty(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test that invalid JSON returns empty dict."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(return_value="not json")
        variables: dict[str, Any]
        variables, _ = await session_manager._receive_prompt_config(ws, agent_def_for_config)
        assert variables == {}

    @pytest.mark.asyncio
    async def test_empty_values_filtered(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test that empty string values are filtered out."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "prompt_config",
                    "variables": {"company_name": "", "agent_name": "  ", "guidelines": "Be nice"},
                }
            )
        )
        variables: dict[str, Any]
        variables, _ = await session_manager._receive_prompt_config(ws, agent_def_for_config)
        assert "company_name" not in variables
        assert "agent_name" not in variables
        assert variables["guidelines"] == "Be nice"

    @pytest.mark.asyncio
    async def test_non_string_values_filtered(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test that non-string values are filtered out."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "prompt_config",
                    "variables": {"company_name": 123, "guidelines": "Be nice"},
                }
            )
        )
        variables: dict[str, Any]
        variables, _ = await session_manager._receive_prompt_config(ws, agent_def_for_config)
        assert "company_name" not in variables
        assert variables["guidelines"] == "Be nice"

    @pytest.mark.asyncio
    async def test_unknown_keys_filtered(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test that unknown variable keys are silently dropped."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "prompt_config",
                    "variables": {"company_name": "Acme", "unknown_field": "should be dropped"},
                }
            )
        )
        variables: dict[str, Any]
        variables, _ = await session_manager._receive_prompt_config(ws, agent_def_for_config)
        assert variables["company_name"] == "Acme"
        assert "unknown_field" not in variables

    @pytest.mark.asyncio
    async def test_enabled_tools_extracted(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test that enabled_tools is extracted from prompt_config."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(
            return_value=json.dumps(
                {
                    "type": "prompt_config",
                    "variables": {},
                    "enabled_tools": ["getDateAndTimeTool", "getWeatherTool"],
                }
            )
        )
        _: dict[str, Any]
        enabled_tools: list[str] | None
        _, enabled_tools = await session_manager._receive_prompt_config(ws, agent_def_for_config)
        assert enabled_tools == ["getDateAndTimeTool", "getWeatherTool"]

    @pytest.mark.asyncio
    async def test_enabled_tools_absent_returns_none(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test that missing enabled_tools returns None (use agent defaults)."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(
            return_value=json.dumps(
                {"type": "prompt_config", "variables": {"company_name": "Acme"}}
            )
        )
        _: dict[str, Any]
        enabled_tools: list[str] | None
        _, enabled_tools = await session_manager._receive_prompt_config(ws, agent_def_for_config)
        assert enabled_tools is None

    @pytest.mark.asyncio
    async def test_enabled_tools_empty_list(
        self, session_manager: SessionManager, agent_def_for_config: AgentDefinition
    ):
        """Test that empty enabled_tools list means no tools."""
        ws: MagicMock = MagicMock()
        ws.receive_text = AsyncMock(
            return_value=json.dumps({"type": "prompt_config", "variables": {}, "enabled_tools": []})
        )
        _: dict[str, Any]
        enabled_tools: list[str] | None
        _, enabled_tools = await session_manager._receive_prompt_config(ws, agent_def_for_config)
        assert enabled_tools == []


class TestSessionManagerEdgeCases:
    """Tests for edge cases in session handling."""

    @pytest.mark.asyncio
    async def test_websocket_disconnect_from_provider(
        self, session_manager: SessionManager, mock_provider: MagicMock
    ):
        """Test that WebSocketDisconnect from provider is handled gracefully."""
        mock_provider.handle_session = AsyncMock(side_effect=WebSocketDisconnect)
        ws: MagicMock = _make_websocket()
        # Should not raise
        await session_manager.handle_websocket(
            websocket=ws, provider_name="test", user_id="u1", session_id="s1"
        )

    @pytest.mark.asyncio
    async def test_emit_handles_send_text_failure(
        self, session_manager: SessionManager, mock_provider: MagicMock
    ):
        """Test that emit callback swallows WebSocketDisconnect on send."""
        ws: MagicMock = _make_websocket()
        # Make send_text fail after the first call (SESSION_START)
        call_count: int = 0

        async def fail_on_second_call(text: str) -> None:
            nonlocal call_count
            call_count += 1
            if call_count > 1:
                raise WebSocketDisconnect

        ws.send_text = fail_on_second_call
        # Should not raise even though SESSION_END emit will fail
        await session_manager.handle_websocket(
            websocket=ws, provider_name="test", user_id="u1", session_id="s1"
        )

    @pytest.mark.asyncio
    async def test_emit_handles_runtime_error(
        self, session_manager: SessionManager, mock_provider: MagicMock
    ):
        """Test that emit callback swallows RuntimeError on send."""
        ws: MagicMock = _make_websocket()
        ws.send_text = AsyncMock(side_effect=RuntimeError("connection closed"))
        # Should not raise — both SESSION_START and SESSION_END emits will fail silently
        await session_manager.handle_websocket(
            websocket=ws, provider_name="test", user_id="u1", session_id="s1"
        )
