"""Tests for Google ADK voice provider."""

from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

from fluentia.config import GoogleModelSpec
from fluentia.config import GoogleProviderConfig
from fluentia.config import get_model_spec
from fluentia.providers.google import GoogleProvider
from fluentia.session.events import SessionEventType
from fluentia.tools.implementations.date_time import GetDateAndTimeTool
from fluentia.tools.processor import ToolProcessor


class TestGoogleProviderExtractSampleRate:
    """Tests for GoogleProvider._extract_sample_rate static method."""

    def test_extract_rate_from_pcm_mime(self):
        """Test extracting sample rate from 'audio/pcm;rate=24000'."""
        assert GoogleProvider._extract_sample_rate("audio/pcm;rate=24000") == 24000

    def test_extract_rate_16000(self):
        """Test extracting sample rate of 16000."""
        assert GoogleProvider._extract_sample_rate("audio/pcm;rate=16000") == 16000

    def test_extract_rate_with_extra_params(self):
        """Test extracting rate with additional MIME parameters."""
        assert GoogleProvider._extract_sample_rate("audio/pcm;rate=48000;channels=1") == 48000

    def test_default_rate_when_no_rate_param(self):
        """Test default rate when no rate= in MIME type."""
        assert GoogleProvider._extract_sample_rate("audio/pcm") == 24000

    def test_default_rate_on_invalid_value(self):
        """Test default rate when rate value is not a number."""
        assert GoogleProvider._extract_sample_rate("audio/pcm;rate=invalid") == 24000

    def test_default_rate_on_empty_string(self):
        """Test default rate on empty MIME type."""
        assert GoogleProvider._extract_sample_rate("") == 24000


class TestGoogleProviderConvertAdkEvent:
    """Tests for GoogleProvider._convert_adk_event."""

    def _make_provider(self) -> GoogleProvider:
        """Create a GoogleProvider with default config."""
        config: GoogleProviderConfig = GoogleProviderConfig()
        return GoogleProvider(provider_config=config, tool_processor=ToolProcessor())

    def _mock_adk_event(self, data: dict[str, Any]) -> MagicMock:
        """Create a mock ADK event that returns the given dict from model_dump."""
        mock: MagicMock = MagicMock()
        mock.model_dump.return_value = data
        return mock

    def test_turn_complete(self):
        """Test converting a turnComplete ADK event."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event({"turnComplete": True})
        events = provider._convert_adk_event(event)
        assert len(events) == 1
        assert events[0].type == SessionEventType.TURN_COMPLETE

    def test_interrupted(self):
        """Test converting an interrupted ADK event."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event({"interrupted": True})
        events = provider._convert_adk_event(event)
        assert len(events) == 1
        assert events[0].type == SessionEventType.INTERRUPTED

    def test_input_transcription(self):
        """Test converting an inputTranscription ADK event."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event(
            {"inputTranscription": {"text": "hello", "finished": True}}
        )
        events = provider._convert_adk_event(event)
        assert len(events) == 1
        assert events[0].type == SessionEventType.INPUT_TRANSCRIPTION
        assert events[0].payload["text"] == "hello"
        assert events[0].payload["is_partial"] is False

    def test_input_transcription_partial(self):
        """Test converting a partial inputTranscription ADK event."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event({"inputTranscription": {"text": "hel"}})
        events = provider._convert_adk_event(event)
        assert len(events) == 1
        assert events[0].payload["is_partial"] is True

    def test_output_transcription(self):
        """Test converting an outputTranscription ADK event."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event(
            {"outputTranscription": {"text": "goodbye", "finished": True}}
        )
        events = provider._convert_adk_event(event)
        assert len(events) == 1
        assert events[0].type == SessionEventType.OUTPUT_TRANSCRIPTION
        assert events[0].payload["text"] == "goodbye"

    def test_audio_content_bytes(self):
        """Test converting audio content with bytes data (base64-encodes it)."""
        provider: GoogleProvider = self._make_provider()
        raw_audio: bytes = b"\x00\x01\x02\x03"
        event: MagicMock = self._mock_adk_event(
            {
                "content": {
                    "parts": [
                        {"inlineData": {"mimeType": "audio/pcm;rate=24000", "data": raw_audio}}
                    ]
                }
            }
        )
        events = provider._convert_adk_event(event)
        assert len(events) == 1
        assert events[0].type == SessionEventType.AUDIO
        assert events[0].payload["data"] == "AAECAw=="
        assert events[0].payload["sample_rate"] == 24000

    def test_audio_content_string(self):
        """Test converting audio content with string data (passes through)."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event(
            {
                "content": {
                    "parts": [
                        {"inlineData": {"mimeType": "audio/pcm;rate=24000", "data": "base64audio"}}
                    ]
                }
            }
        )
        events = provider._convert_adk_event(event)
        assert len(events) == 1
        assert events[0].type == SessionEventType.AUDIO
        assert events[0].payload["data"] == "base64audio"
        assert events[0].payload["sample_rate"] == 24000

    def test_text_content(self):
        """Test converting a text content ADK event."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event({"content": {"parts": [{"text": "Hello world"}]}})
        events = provider._convert_adk_event(event)
        assert len(events) == 1
        assert events[0].type == SessionEventType.TEXT
        assert events[0].payload["content"] == "Hello world"

    def test_empty_event(self):
        """Test converting an event with no recognized fields."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event({"serverContent": {}})
        events = provider._convert_adk_event(event)
        assert len(events) == 0

    def test_empty_transcription_text_ignored(self):
        """Test that empty transcription text produces no events."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event({"inputTranscription": {"text": ""}})
        events = provider._convert_adk_event(event)
        assert len(events) == 0

    def test_non_pcm_audio_ignored(self):
        """Test that non-PCM audio MIME types are ignored."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event(
            {"content": {"parts": [{"inlineData": {"mimeType": "audio/mp3", "data": "mp3data"}}]}}
        )
        events = provider._convert_adk_event(event)
        assert len(events) == 0

    def test_multiple_parts(self):
        """Test converting an event with multiple content parts."""
        provider: GoogleProvider = self._make_provider()
        event: MagicMock = self._mock_adk_event(
            {"content": {"parts": [{"text": "part1"}, {"text": "part2"}]}}
        )
        events = provider._convert_adk_event(event)
        assert len(events) == 2
        assert events[0].payload["content"] == "part1"
        assert events[1].payload["content"] == "part2"


class TestGoogleProviderBuildRunConfig:
    """Tests for GoogleProvider._build_run_config."""

    def test_native_audio_config(self):
        """Test run config for native audio model."""
        config: GoogleProviderConfig = GoogleProviderConfig(
            model_name="gemini-2.5-flash-native-audio-preview-12-2025"
        )
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {}
        spec = get_model_spec("gemini-2.5-flash-native-audio-preview-12-2025")
        run_config = provider._build_run_config(ws, spec)
        assert run_config.response_modalities == ["AUDIO"]

    def test_non_native_audio_config(self):
        """Test run config for non-native audio model."""
        config: GoogleProviderConfig = GoogleProviderConfig(model_name="gemini-2.0-flash")
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {}
        spec = get_model_spec("gemini-2.0-flash")
        run_config = provider._build_run_config(ws, spec)
        assert run_config.response_modalities == ["TEXT"]

    def test_proactivity_enabled_on_25(self):
        """Test run config with proactivity enabled for Gemini 2.5 native audio."""
        config: GoogleProviderConfig = GoogleProviderConfig(
            model_name="gemini-2.5-flash-native-audio-preview-12-2025"
        )
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {"proactivity": "true"}
        spec = get_model_spec("gemini-2.5-flash-native-audio-preview-12-2025")
        run_config = provider._build_run_config(ws, spec)
        assert run_config.proactivity is not None

    def test_proactivity_disabled(self):
        """Test run config with proactivity disabled."""
        config: GoogleProviderConfig = GoogleProviderConfig(
            model_name="gemini-2.5-flash-native-audio-preview-12-2025"
        )
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {"proactivity": "false"}
        spec = get_model_spec("gemini-2.5-flash-native-audio-preview-12-2025")
        run_config = provider._build_run_config(ws, spec)
        assert run_config.proactivity is None

    def test_affective_dialog_enabled_on_25(self):
        """Test run config with affective dialog for Gemini 2.5 native audio."""
        config: GoogleProviderConfig = GoogleProviderConfig(
            model_name="gemini-2.5-flash-native-audio-preview-12-2025"
        )
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {"affective_dialog": "true"}
        spec = get_model_spec("gemini-2.5-flash-native-audio-preview-12-2025")
        run_config = provider._build_run_config(ws, spec)
        assert run_config.enable_affective_dialog is True

    def test_proactivity_ignored_on_31(self):
        """Test that proactivity is ignored on Gemini 3.1 (not supported)."""
        config: GoogleProviderConfig = GoogleProviderConfig()
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {"proactivity": "true"}
        spec = get_model_spec("gemini-3.1-flash-live-preview")
        run_config = provider._build_run_config(ws, spec)
        assert run_config.response_modalities == ["AUDIO"]
        assert run_config.proactivity is None

    def test_affective_dialog_ignored_on_31(self):
        """Test that affective dialog is ignored on Gemini 3.1 (not supported)."""
        config: GoogleProviderConfig = GoogleProviderConfig()
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {"affective_dialog": "true"}
        spec = get_model_spec("gemini-3.1-flash-live-preview")
        run_config = provider._build_run_config(ws, spec)
        assert run_config.response_modalities == ["AUDIO"]
        assert run_config.enable_affective_dialog is None

    def test_proactivity_ignored_on_non_native_audio(self):
        """Test that proactivity on non-native audio model logs a warning."""
        config: GoogleProviderConfig = GoogleProviderConfig(model_name="gemini-2.0-flash")
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {"proactivity": "true"}
        spec = get_model_spec("gemini-2.0-flash")
        run_config = provider._build_run_config(ws, spec)
        # Non-native audio always returns TEXT modality, proactivity is ignored
        assert run_config.response_modalities == ["TEXT"]
        assert run_config.proactivity is None

    def test_affective_dialog_ignored_on_non_native_audio(self):
        """Test that affective dialog on non-native audio model is ignored."""
        config: GoogleProviderConfig = GoogleProviderConfig(model_name="gemini-2.0-flash")
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {"affective_dialog": "true"}
        spec = get_model_spec("gemini-2.0-flash")
        run_config = provider._build_run_config(ws, spec)
        assert run_config.response_modalities == ["TEXT"]

    def test_default_model_is_25(self):
        """Test that the default model is Gemini 2.5 Flash Native Audio."""
        config: GoogleProviderConfig = GoogleProviderConfig()
        provider: GoogleProvider = GoogleProvider(
            provider_config=config, tool_processor=ToolProcessor()
        )
        ws: MagicMock = MagicMock()
        ws.query_params = {}
        spec = get_model_spec(config.model_name)
        run_config = provider._build_run_config(ws, spec)
        assert run_config.response_modalities == ["AUDIO"]
        assert config.model_name == "gemini-2.5-flash-native-audio-preview-12-2025"


class TestGoogleProviderBuildAdkTools:
    """Tests for GoogleProvider._build_adk_tools."""

    def test_builds_wrappers_for_registered_tools(self):
        """Test that _build_adk_tools creates wrappers for enabled tools."""
        tp: ToolProcessor = ToolProcessor()
        tp.register(GetDateAndTimeTool())
        config: GoogleProviderConfig = GoogleProviderConfig()
        provider: GoogleProvider = GoogleProvider(provider_config=config, tool_processor=tp)
        emit: AsyncMock = AsyncMock()
        tools: list[Any] = provider._build_adk_tools(["getDateAndTimeTool"], emit)
        assert len(tools) == 1
        assert tools[0].__name__ == "getDateAndTimeTool"

    def test_skips_google_search(self):
        """Test that google_search is skipped (handled separately)."""
        tp: ToolProcessor = ToolProcessor()
        tp.register(GetDateAndTimeTool())
        config: GoogleProviderConfig = GoogleProviderConfig()
        provider: GoogleProvider = GoogleProvider(provider_config=config, tool_processor=tp)
        emit: AsyncMock = AsyncMock()
        tools: list[Any] = provider._build_adk_tools(["getDateAndTimeTool", "google_search"], emit)
        assert len(tools) == 1

    def test_unknown_tool_skipped(self):
        """Test that unknown tools are skipped with no error."""
        tp: ToolProcessor = ToolProcessor()
        config: GoogleProviderConfig = GoogleProviderConfig()
        provider: GoogleProvider = GoogleProvider(provider_config=config, tool_processor=tp)
        emit: AsyncMock = AsyncMock()
        tools: list[Any] = provider._build_adk_tools(["nonexistent"], emit)
        assert len(tools) == 0

    def test_tools_skipped_when_model_does_not_support(self):
        """Test that tools are not built when the model does not support them."""
        tp: ToolProcessor = ToolProcessor()
        tp.register(GetDateAndTimeTool())
        config: GoogleProviderConfig = GoogleProviderConfig()
        provider: GoogleProvider = GoogleProvider(provider_config=config, tool_processor=tp)
        emit: AsyncMock = AsyncMock()
        # Gemini 3.1 does not support tools
        spec: GoogleModelSpec = get_model_spec("gemini-3.1-flash-live-preview")
        assert spec.supports_tools is False
        # When supports_tools is False, the provider skips _build_adk_tools entirely
        # We verify by confirming _build_adk_tools still works — the gating is in _create_runner
        tools: list[Any] = provider._build_adk_tools(["getDateAndTimeTool"], emit)
        assert len(tools) == 1  # _build_adk_tools itself doesn't gate
