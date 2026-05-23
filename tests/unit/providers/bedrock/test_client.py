"""Tests for Nova Sonic streaming client."""

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from fluentia.providers.bedrock.client import NovaSonicClient
from fluentia.providers.bedrock.client import _InternalToolUseEvent
from fluentia.providers.bedrock.config import BedrockSessionConfig
from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType


@pytest.fixture
def config() -> BedrockSessionConfig:
    """Fixture for a default BedrockSessionConfig."""
    return BedrockSessionConfig()


@pytest.fixture
def client(config: BedrockSessionConfig) -> NovaSonicClient:
    """Fixture for a NovaSonicClient (not connected)."""
    return NovaSonicClient(config=config)


class TestNovaSonicClientInit:
    """Tests for NovaSonicClient initialization."""

    def test_initial_state(self, client: NovaSonicClient):
        """Test initial state of the client."""
        assert client.is_active is False
        assert client.barge_in_detected is False

    def test_config_stored(self, client: NovaSonicClient, config: BedrockSessionConfig):
        """Test that config is stored."""
        assert client.config is config


class TestNovaSonicClientSendAudio:
    """Tests for send_audio method."""

    @pytest.mark.asyncio
    async def test_send_audio_when_inactive(self, client: NovaSonicClient):
        """Test that send_audio does nothing when client is inactive."""
        await client.send_audio(b"audio-data")
        # Should not raise, just return early
        assert client._audio_input_queue.empty()

    @pytest.mark.asyncio
    async def test_send_audio_when_active(self, client: NovaSonicClient):
        """Test that send_audio queues data when client is active."""
        client._is_active = True
        await client.send_audio(b"audio-data")
        assert not client._audio_input_queue.empty()
        data: bytes = await client._audio_input_queue.get()
        assert data == b"audio-data"


class TestNovaSonicClientClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_when_inactive(self, client: NovaSonicClient):
        """Test that close does nothing when already inactive."""
        await client.close()
        assert client.is_active is False

    @pytest.mark.asyncio
    async def test_close_sets_inactive(self, client: NovaSonicClient):
        """Test that close sets _is_active to False."""
        client._is_active = True
        client._stream_response = None
        await client.close()
        assert client.is_active is False


class TestNovaSonicClientHandleContentStart:
    """Tests for _handle_content_start method."""

    def test_sets_role(self, client: NovaSonicClient):
        """Test that content start sets current role."""
        client._handle_content_start({"role": "USER"})
        assert client._current_role == "USER"

    def test_sets_role_assistant(self, client: NovaSonicClient):
        """Test that content start sets assistant role."""
        client._handle_content_start({"role": "ASSISTANT"})
        assert client._current_role == "ASSISTANT"

    def test_speculative_stage_enables_display(self, client: NovaSonicClient):
        """Test that SPECULATIVE generation stage enables text display."""
        additional: str = json.dumps({"generationStage": "SPECULATIVE"})
        client._handle_content_start({"role": "ASSISTANT", "additionalModelFields": additional})
        assert client._display_assistant_text is True

    def test_non_speculative_stage_disables_display(self, client: NovaSonicClient):
        """Test that non-SPECULATIVE stage disables text display."""
        additional: str = json.dumps({"generationStage": "FINAL"})
        client._handle_content_start({"role": "ASSISTANT", "additionalModelFields": additional})
        assert client._display_assistant_text is False

    def test_invalid_json_additional_fields(self, client: NovaSonicClient):
        """Test that invalid JSON in additionalModelFields is handled."""
        client._handle_content_start({"role": "ASSISTANT", "additionalModelFields": "not json"})
        assert client._display_assistant_text is False

    def test_no_additional_fields(self, client: NovaSonicClient):
        """Test that missing additionalModelFields defaults to no display."""
        client._handle_content_start({"role": "ASSISTANT"})
        assert client._display_assistant_text is False


class TestNovaSonicClientHandleTextOutput:
    """Tests for _handle_text_output method."""

    @pytest.mark.asyncio
    async def test_user_transcription(self, client: NovaSonicClient):
        """Test that USER text output emits INPUT_TRANSCRIPTION."""
        client._current_role = "USER"
        await client._handle_text_output({"content": "hello world"})
        event: SessionEvent = await client._event_queue.get()
        assert event.type == SessionEventType.INPUT_TRANSCRIPTION
        assert event.payload["text"] == "hello world"

    @pytest.mark.asyncio
    async def test_assistant_speculative_transcription(self, client: NovaSonicClient):
        """Test that ASSISTANT speculative text emits OUTPUT_TRANSCRIPTION."""
        client._current_role = "ASSISTANT"
        client._display_assistant_text = True
        await client._handle_text_output({"content": "response text"})
        event: SessionEvent = await client._event_queue.get()
        assert event.type == SessionEventType.OUTPUT_TRANSCRIPTION
        assert event.payload["text"] == "response text"

    @pytest.mark.asyncio
    async def test_assistant_non_speculative_ignored(self, client: NovaSonicClient):
        """Test that ASSISTANT non-speculative text is ignored."""
        client._current_role = "ASSISTANT"
        client._display_assistant_text = False
        await client._handle_text_output({"content": "silent text"})
        assert client._event_queue.empty()

    @pytest.mark.asyncio
    async def test_interrupted_detection(self, client: NovaSonicClient):
        """Test that interrupted marker emits INTERRUPTED event."""
        await client._handle_text_output({"content": '{ "interrupted" : true }'})
        assert client.barge_in_detected is True
        event: SessionEvent = await client._event_queue.get()
        assert event.type == SessionEventType.INTERRUPTED


class TestNovaSonicClientHandleAudioOutput:
    """Tests for _handle_audio_output method."""

    @pytest.mark.asyncio
    async def test_audio_output_emitted(self, client: NovaSonicClient):
        """Test that audio output emits AUDIO event."""
        await client._handle_audio_output({"content": "base64audio"})
        event: SessionEvent = await client._event_queue.get()
        assert event.type == SessionEventType.AUDIO
        assert event.payload["data"] == "base64audio"
        assert event.payload["sample_rate"] == 24000

    @pytest.mark.asyncio
    async def test_empty_audio_ignored(self, client: NovaSonicClient):
        """Test that empty audio content is ignored."""
        await client._handle_audio_output({"content": ""})
        assert client._event_queue.empty()


class TestNovaSonicClientHandleToolUse:
    """Tests for _handle_tool_use method."""

    def test_stores_tool_info(self, client: NovaSonicClient):
        """Test that tool use info is stored."""
        tool_data: dict[str, Any] = {
            "toolUseId": "tu-1",
            "toolName": "get_time",
            "content": '{"timezone": "UTC"}',
        }
        client._handle_tool_use(tool_data)
        assert client._current_tool_use_id == "tu-1"
        assert client._current_tool_name == "get_time"
        assert client._current_tool_content == tool_data


class TestNovaSonicClientHandleContentEnd:
    """Tests for _handle_content_end method."""

    @pytest.mark.asyncio
    async def test_tool_content_end_emits_event(self, client: NovaSonicClient):
        """Test that TOOL content end emits _InternalToolUseEvent."""
        client._current_tool_use_id = "tu-1"
        client._current_tool_name = "get_time"
        client._current_tool_content = {"content": '{"timezone": "UTC"}'}

        await client._handle_content_end({"type": "TOOL"})

        event: _InternalToolUseEvent = await client._event_queue.get()
        assert isinstance(event, _InternalToolUseEvent)
        assert event.tool_use_id == "tu-1"
        assert event.tool_name == "get_time"
        assert event.tool_input == {"timezone": "UTC"}

    @pytest.mark.asyncio
    async def test_tool_content_end_resets_state(self, client: NovaSonicClient):
        """Test that tool state is reset after content end."""
        client._current_tool_use_id = "tu-1"
        client._current_tool_name = "get_time"
        client._current_tool_content = {}

        await client._handle_content_end({"type": "TOOL"})

        assert client._current_tool_use_id == ""
        assert client._current_tool_name == ""
        assert client._current_tool_content == {}

    @pytest.mark.asyncio
    async def test_audio_content_end_emits_turn_complete(self, client: NovaSonicClient):
        """Test that AUDIO content end emits TURN_COMPLETE."""
        await client._handle_content_end({"type": "AUDIO"})
        event: SessionEvent = await client._event_queue.get()
        assert event.type == SessionEventType.TURN_COMPLETE

    @pytest.mark.asyncio
    async def test_tool_content_end_invalid_json(self, client: NovaSonicClient):
        """Test that invalid JSON tool content falls back gracefully."""
        client._current_tool_use_id = "tu-1"
        client._current_tool_name = "tool"
        client._current_tool_content = {"content": "not json"}

        await client._handle_content_end({"type": "TOOL"})

        event: _InternalToolUseEvent = await client._event_queue.get()
        assert event.tool_input == "not json"  # type: ignore[comparison-overlap]


class TestNovaSonicClientHandleResponseData:
    """Tests for _handle_response_data method."""

    @pytest.mark.asyncio
    async def test_invalid_json_ignored(self, client: NovaSonicClient):
        """Test that invalid JSON response data is ignored."""
        await client._handle_response_data("not json")
        assert client._event_queue.empty()

    @pytest.mark.asyncio
    async def test_no_event_key_ignored(self, client: NovaSonicClient):
        """Test that response without 'event' key is ignored."""
        await client._handle_response_data('{"data": "something"}')
        assert client._event_queue.empty()

    @pytest.mark.asyncio
    async def test_content_start_dispatched(self, client: NovaSonicClient):
        """Test that contentStart event is dispatched."""
        data: str = json.dumps({"event": {"contentStart": {"role": "USER"}}})
        await client._handle_response_data(data)
        assert client._current_role == "USER"

    @pytest.mark.asyncio
    async def test_text_output_dispatched(self, client: NovaSonicClient):
        """Test that textOutput event is dispatched."""
        client._current_role = "USER"
        data: str = json.dumps({"event": {"textOutput": {"content": "test"}}})
        await client._handle_response_data(data)
        event: SessionEvent = await client._event_queue.get()
        assert event.type == SessionEventType.INPUT_TRANSCRIPTION

    @pytest.mark.asyncio
    async def test_audio_output_dispatched(self, client: NovaSonicClient):
        """Test that audioOutput event is dispatched."""
        data: str = json.dumps({"event": {"audioOutput": {"content": "audio"}}})
        await client._handle_response_data(data)
        event: SessionEvent = await client._event_queue.get()
        assert event.type == SessionEventType.AUDIO

    @pytest.mark.asyncio
    async def test_tool_use_dispatched(self, client: NovaSonicClient):
        """Test that toolUse event is dispatched."""
        data: str = json.dumps(
            {"event": {"toolUse": {"toolUseId": "tu-1", "toolName": "get_time"}}}
        )
        await client._handle_response_data(data)
        assert client._current_tool_use_id == "tu-1"


class TestNovaSonicClientContentEndEdgeCases:
    """Additional edge case tests for _handle_content_end."""

    @pytest.mark.asyncio
    async def test_tool_content_end_no_tool_id_skipped(self, client: NovaSonicClient):
        """Test that TOOL content end with empty tool_use_id is skipped."""
        client._current_tool_use_id = ""
        await client._handle_content_end({"type": "TOOL"})
        assert client._event_queue.empty()

    @pytest.mark.asyncio
    async def test_tool_content_end_no_content_key(self, client: NovaSonicClient):
        """Test TOOL content end when tool_content has no 'content' key."""
        client._current_tool_use_id = "tu-1"
        client._current_tool_name = "tool"
        client._current_tool_content = {}
        await client._handle_content_end({"type": "TOOL"})
        event: _InternalToolUseEvent = await client._event_queue.get()
        assert event.tool_input == {}

    @pytest.mark.asyncio
    async def test_unknown_content_type_ignored(self, client: NovaSonicClient):
        """Test that unknown content types are silently ignored."""
        await client._handle_content_end({"type": "UNKNOWN"})
        assert client._event_queue.empty()


class TestNovaSonicClientSendMethods:
    """Tests for the _send_* event building methods."""

    @pytest.mark.asyncio
    async def test_send_raw_event_when_inactive(self, client: NovaSonicClient):
        """Test that _send_raw_event does nothing when inactive."""
        # No stream_response, not active — should return early without error
        await client._send_raw_event('{"test": true}')

    @pytest.mark.asyncio
    async def test_send_raw_event_sends_to_stream(self, client: NovaSonicClient):
        """Test that _send_raw_event sends encoded bytes to the stream."""
        mock_stream: MagicMock = MagicMock()
        mock_stream.input_stream = MagicMock()
        mock_stream.input_stream.send = AsyncMock()
        client._stream_response = mock_stream
        client._is_active = True

        await client._send_raw_event('{"test": true}')
        mock_stream.input_stream.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_session_start_event(self, client: NovaSonicClient):
        """Test _send_session_start_event builds correct JSON."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        await client._send_session_start_event()
        assert len(sent_events) == 1
        data: dict[str, Any] = json.loads(sent_events[0])
        assert "sessionStart" in data["event"]
        assert "inferenceConfiguration" in data["event"]["sessionStart"]

    @pytest.mark.asyncio
    async def test_send_prompt_start_event_with_tools(self, client: NovaSonicClient):
        """Test _send_prompt_start_event includes tool configuration."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        tools: list[dict[str, Any]] = [{"toolSpec": {"name": "test"}}]
        await client._send_prompt_start_event(tools)
        data: dict[str, Any] = json.loads(sent_events[0])
        assert "toolConfiguration" in data["event"]["promptStart"]

    @pytest.mark.asyncio
    async def test_send_prompt_start_event_without_tools(self, client: NovaSonicClient):
        """Test _send_prompt_start_event without tools omits toolConfiguration."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        await client._send_prompt_start_event([])
        data: dict[str, Any] = json.loads(sent_events[0])
        assert "toolConfiguration" not in data["event"]["promptStart"]

    @pytest.mark.asyncio
    async def test_send_system_prompt(self, client: NovaSonicClient):
        """Test _send_system_prompt sends content start, text, and content end."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        await client._send_system_prompt("You are a helpful assistant.")
        assert len(sent_events) == 3  # contentStart, textInput, contentEnd
        text_event: dict[str, Any] = json.loads(sent_events[1])
        assert text_event["event"]["textInput"]["content"] == "You are a helpful assistant."

    @pytest.mark.asyncio
    async def test_send_audio_content_start_event(self, client: NovaSonicClient):
        """Test _send_audio_content_start_event builds correct audio config."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        await client._send_audio_content_start_event()
        data: dict[str, Any] = json.loads(sent_events[0])
        content_start: dict[str, Any] = data["event"]["contentStart"]
        assert content_start["type"] == "AUDIO"
        assert content_start["role"] == "USER"

    @pytest.mark.asyncio
    async def test_send_audio_content_start_with_language(self, config: BedrockSessionConfig):
        """Test _send_audio_content_start includes language when configured."""
        config_with_lang: BedrockSessionConfig = BedrockSessionConfig(language="en-US")
        lang_client: NovaSonicClient = NovaSonicClient(config=config_with_lang)
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        lang_client._send_raw_event = capture  # type: ignore[assignment]
        await lang_client._send_audio_content_start_event()
        data: dict[str, Any] = json.loads(sent_events[0])
        audio_config: dict[str, Any] = data["event"]["contentStart"]["audioInputConfiguration"]
        assert audio_config["language"] == "en-US"

    @pytest.mark.asyncio
    async def test_send_audio_input_event(self, client: NovaSonicClient):
        """Test _send_audio_input_event base64-encodes audio."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        await client._send_audio_input_event(b"\x00\x01\x02")
        data: dict[str, Any] = json.loads(sent_events[0])
        assert data["event"]["audioInput"]["content"] == "AAEC"

    @pytest.mark.asyncio
    async def test_send_tool_content_start_event(self, client: NovaSonicClient):
        """Test _send_tool_content_start_event builds tool content start."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        await client._send_tool_content_start_event("cn-1", "tu-1")
        data: dict[str, Any] = json.loads(sent_events[0])
        content_start: dict[str, Any] = data["event"]["contentStart"]
        assert content_start["type"] == "TOOL"
        assert content_start["toolResultInputConfiguration"]["toolUseId"] == "tu-1"

    @pytest.mark.asyncio
    async def test_send_tool_result_event(self, client: NovaSonicClient):
        """Test _send_tool_result_event sends JSON result."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        await client._send_tool_result_event("cn-1", {"time": "12:00"})
        data: dict[str, Any] = json.loads(sent_events[0])
        assert json.loads(data["event"]["toolResult"]["content"]) == {"time": "12:00"}

    @pytest.mark.asyncio
    async def test_send_prompt_end_event(self, client: NovaSonicClient):
        """Test _send_prompt_end_event."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        await client._send_prompt_end_event()
        data: dict[str, Any] = json.loads(sent_events[0])
        assert "promptEnd" in data["event"]

    @pytest.mark.asyncio
    async def test_send_session_end_event(self, client: NovaSonicClient):
        """Test _send_session_end_event."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._send_raw_event = capture  # type: ignore[assignment]
        await client._send_session_end_event()
        data: dict[str, Any] = json.loads(sent_events[0])
        assert "sessionEnd" in data["event"]


class TestNovaSonicClientSendToolResult:
    """Tests for send_tool_result method."""

    @pytest.mark.asyncio
    async def test_send_tool_result_when_inactive(self, client: NovaSonicClient):
        """Test that send_tool_result returns early when inactive."""
        await client.send_tool_result("tu-1", {"result": "ok"})
        # Should not raise

    @pytest.mark.asyncio
    async def test_send_tool_result_when_active(self, client: NovaSonicClient):
        """Test that send_tool_result sends three events."""
        sent_events: list[str] = []

        async def capture(event_json: str) -> None:
            sent_events.append(event_json)

        client._is_active = True
        client._send_raw_event = capture  # type: ignore[assignment]
        await client.send_tool_result("tu-1", {"time": "12:00"})
        # Should send: tool content start, tool result, content end
        assert len(sent_events) == 3


class TestNovaSonicClientReceiveEvents:
    """Tests for receive_events method."""

    @pytest.mark.asyncio
    async def test_receive_events_yields_queued_events(self, client: NovaSonicClient):
        """Test that receive_events yields events from the queue."""
        client._is_active = True
        event: SessionEvent = SessionEvent(type=SessionEventType.TURN_COMPLETE)
        await client._event_queue.put(event)

        received: list[SessionEvent | _InternalToolUseEvent] = []
        async for evt in client.receive_events():
            received.append(evt)
            client._is_active = False  # Stop after first event

        assert len(received) == 1
        assert received[0].type == SessionEventType.TURN_COMPLETE


class TestNovaSonicClientConnect:
    """Tests for connect method."""

    @pytest.mark.asyncio
    async def test_connect_initializes_stream(self, client: NovaSonicClient):
        """Test that connect sets up the stream and starts background tasks."""
        mock_bedrock: MagicMock = MagicMock()
        mock_stream: MagicMock = MagicMock()
        mock_bedrock.invoke_model_with_bidirectional_stream = AsyncMock(return_value=mock_stream)
        client._bedrock_client = mock_bedrock

        # Mock _send methods to avoid actual stream operations
        client._send_session_start_event = AsyncMock()  # type: ignore[assignment]
        client._send_prompt_start_event = AsyncMock()  # type: ignore[assignment]
        client._send_system_prompt = AsyncMock()  # type: ignore[assignment]
        client._send_audio_content_start_event = AsyncMock()  # type: ignore[assignment]
        client._process_responses = AsyncMock()  # type: ignore[assignment]
        client._process_audio_input = AsyncMock()  # type: ignore[assignment]

        await client.connect(system_prompt="Hello", tool_specs=[])

        assert client._is_active is True
        client._send_session_start_event.assert_called_once()
        client._send_prompt_start_event.assert_called_once()
        client._send_system_prompt.assert_called_once_with("Hello")
        client._send_audio_content_start_event.assert_called_once()

        # Clean up background tasks
        client._is_active = False
        if client._response_task:
            client._response_task.cancel()
            try:
                await client._response_task
            except asyncio.CancelledError:
                pass
        if client._audio_input_task:
            client._audio_input_task.cancel()
            try:
                await client._audio_input_task
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_connect_initializes_bedrock_client_if_none(self, client: NovaSonicClient):
        """Test that connect calls _initialize_bedrock_client when client is None."""
        with patch.object(client, "_initialize_bedrock_client") as mock_init:
            # After _initialize_bedrock_client, client is still None -> RuntimeError
            with pytest.raises(RuntimeError, match="Failed to initialize"):
                await client.connect(system_prompt="test", tool_specs=[])
            mock_init.assert_called_once()


class TestNovaSonicClientCloseEdgeCases:
    """Tests for close method with various states."""

    @pytest.mark.asyncio
    async def test_close_cancels_audio_input_task(self, client: NovaSonicClient):
        """Test that close cancels the audio input task."""
        client._is_active = True
        client._stream_response = None

        async def forever() -> None:
            await asyncio.sleep(999)

        client._audio_input_task = asyncio.create_task(forever())
        await client.close()
        assert client._audio_input_task.cancelled()

    @pytest.mark.asyncio
    async def test_close_handles_failed_closing_events(self, client: NovaSonicClient):
        """Test that close handles exceptions during closing event sends."""
        client._is_active = True
        client._stream_response = None

        async def fail(*_args: Any) -> None:
            raise RuntimeError("send failed")

        client._send_raw_event = fail  # type: ignore[assignment]
        # Should not raise
        await client.close()
        assert client._is_active is False

    @pytest.mark.asyncio
    async def test_close_closes_input_stream(self, client: NovaSonicClient):
        """Test that close closes the input stream."""
        client._is_active = True
        mock_stream: MagicMock = MagicMock()
        mock_stream.input_stream = MagicMock()
        mock_stream.input_stream.close = AsyncMock()
        client._stream_response = mock_stream
        client._send_raw_event = AsyncMock()  # type: ignore[assignment]

        await client.close()
        mock_stream.input_stream.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_handles_input_stream_error(self, client: NovaSonicClient):
        """Test that close handles errors when closing input stream."""
        client._is_active = True
        mock_stream: MagicMock = MagicMock()
        mock_stream.input_stream = MagicMock()
        mock_stream.input_stream.close = AsyncMock(side_effect=RuntimeError("closed"))
        client._stream_response = mock_stream
        client._send_raw_event = AsyncMock()  # type: ignore[assignment]

        # Should not raise
        await client.close()

    @pytest.mark.asyncio
    async def test_close_waits_for_response_task(self, client: NovaSonicClient):
        """Test that close waits for and cancels response task if needed."""
        client._is_active = True
        client._stream_response = None

        async def slow_task() -> None:
            await asyncio.sleep(999)

        client._response_task = asyncio.create_task(slow_task())
        client._send_raw_event = AsyncMock()  # type: ignore[assignment]

        await client.close()
        assert client._response_task.cancelled() or client._response_task.done()


class TestInternalToolUseEvent:
    """Tests for _InternalToolUseEvent."""

    def test_creation(self):
        """Test creating an _InternalToolUseEvent."""
        event: _InternalToolUseEvent = _InternalToolUseEvent(
            tool_use_id="tu-1", tool_name="get_time", tool_input={"tz": "UTC"}
        )
        assert event.tool_use_id == "tu-1"
        assert event.tool_name == "get_time"
        assert event.tool_input == {"tz": "UTC"}
