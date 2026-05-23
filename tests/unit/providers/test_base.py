"""Tests for base provider ABC and SessionContext."""

from unittest.mock import AsyncMock

import pytest

from fluentia.agents.base import AgentDefinition
from fluentia.providers.base import BaseProvider
from fluentia.providers.base import SessionContext
from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType


class TestSessionContext:
    """Tests for SessionContext dataclass."""

    def test_creation(self):
        """Test creating a SessionContext with required fields."""
        emit: AsyncMock = AsyncMock()
        agent_def: AgentDefinition = AgentDefinition(
            name="test",
            display_name="Test Agent",
            description="A test agent",
            template_path=None,
            default_variables={},
        )
        context: SessionContext = SessionContext(
            user_id="user-1", session_id="sess-1", agent_definition=agent_def, emit=emit
        )
        assert context.user_id == "user-1"
        assert context.session_id == "sess-1"
        assert context.agent_definition is agent_def
        assert context.emit is emit

    def test_frozen(self):
        """Test that SessionContext is frozen (immutable)."""
        emit: AsyncMock = AsyncMock()
        agent_def: AgentDefinition = AgentDefinition(
            name="test",
            display_name="Test",
            description="test",
            template_path=None,
            default_variables={},
        )
        context: SessionContext = SessionContext(
            user_id="u1", session_id="s1", agent_definition=agent_def, emit=emit
        )
        with pytest.raises(AttributeError):
            context.user_id = "u2"  # type: ignore[misc]

    @pytest.mark.asyncio
    async def test_emit_callable(self):
        """Test that emit callback can be called."""
        emit: AsyncMock = AsyncMock()
        agent_def: AgentDefinition = AgentDefinition(
            name="test",
            display_name="Test",
            description="test",
            template_path=None,
            default_variables={},
        )
        context: SessionContext = SessionContext(
            user_id="u1", session_id="s1", agent_definition=agent_def, emit=emit
        )
        event: SessionEvent = SessionEvent(type=SessionEventType.AUDIO, payload={"data": "abc"})
        await context.emit(event)
        emit.assert_called_once_with(event)


class TestBaseProvider:
    """Tests for BaseProvider ABC."""

    def test_cannot_instantiate(self):
        """Test that BaseProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseProvider()  # type: ignore[abstract]

    def test_subclass_must_implement_handle_session(self):
        """Test that subclass without handle_session cannot be instantiated."""

        class IncompleteProvider(BaseProvider):
            pass

        with pytest.raises(TypeError):
            IncompleteProvider()  # type: ignore[abstract]

    def test_subclass_with_handle_session(self):
        """Test that a complete subclass can be instantiated."""

        class CompleteProvider(BaseProvider):
            async def handle_session(self, websocket, session_context):
                pass

        provider: CompleteProvider = CompleteProvider()
        assert isinstance(provider, BaseProvider)
