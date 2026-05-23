"""Tests for configuration models."""

from fluentia.config import DEFAULT_GOOGLE_MODEL
from fluentia.config import GOOGLE_MODEL_CATALOG
from fluentia.config import AppConfig
from fluentia.config import BedrockProviderConfig
from fluentia.config import GoogleProviderConfig
from fluentia.config import get_model_spec


class TestGoogleProviderConfig:
    def test_default_model(self):
        config = GoogleProviderConfig()
        assert config.model_name == "gemini-2.5-flash-native-audio-preview-12-2025"

    def test_is_native_audio_true(self):
        config = GoogleProviderConfig()
        assert config.is_native_audio is True

    def test_is_native_audio_false(self):
        config = GoogleProviderConfig(model_name="gemini-2.0-flash")
        assert config.is_native_audio is False

    def test_default_api_key_empty(self):
        config = GoogleProviderConfig()
        assert config.api_key == ""

    def test_model_spec_from_catalog(self):
        config = GoogleProviderConfig(model_name="gemini-2.5-flash-native-audio-preview-12-2025")
        spec = config.model_spec
        assert spec.display_name == "Gemini 2.5 Flash Native Audio"
        assert spec.supports_proactivity is True
        assert spec.supports_affective_dialog is True

    def test_model_spec_default_has_proactivity(self):
        config = GoogleProviderConfig()
        spec = config.model_spec
        assert spec.supports_proactivity is True
        assert spec.supports_affective_dialog is True

    def test_model_spec_unknown_fallback(self):
        config = GoogleProviderConfig(model_name="gemini-future-model")
        spec = config.model_spec
        assert spec.model_id == "gemini-future-model"
        assert spec.supports_native_audio is False
        assert spec.supports_proactivity is False

    def test_model_spec_unknown_native_audio_fallback(self):
        config = GoogleProviderConfig(model_name="gemini-99-native-audio-preview")
        spec = config.model_spec
        assert spec.supports_native_audio is True


class TestGoogleModelCatalog:
    def test_catalog_has_default(self):
        assert DEFAULT_GOOGLE_MODEL == "gemini-2.5-flash-native-audio-preview-12-2025"

    def test_catalog_entries(self):
        assert "gemini-3.1-flash-live-preview" in GOOGLE_MODEL_CATALOG
        assert "gemini-2.5-flash-native-audio-preview-12-2025" in GOOGLE_MODEL_CATALOG

    def test_get_model_spec_known(self):
        spec = get_model_spec("gemini-2.5-flash-native-audio-preview-12-2025")
        assert spec.display_name == "Gemini 2.5 Flash Native Audio"
        assert spec.supports_native_audio is True
        assert spec.is_default is True

    def test_get_model_spec_unknown(self):
        spec = get_model_spec("unknown-model")
        assert spec.model_id == "unknown-model"
        assert spec.supports_proactivity is False

    def test_supports_tools_default_true(self):
        spec = get_model_spec("gemini-2.5-flash-native-audio-preview-12-2025")
        assert spec.supports_tools is True

    def test_supports_tools_false_for_31(self):
        spec = get_model_spec("gemini-3.1-flash-live-preview")
        assert spec.supports_tools is False

    def test_supports_tools_unknown_defaults_true(self):
        spec = get_model_spec("gemini-future-model")
        assert spec.supports_tools is True


class TestBedrockProviderConfig:
    def test_defaults(self):
        config = BedrockProviderConfig()
        assert config.region == "us-east-1"
        assert config.voice_id == "matthew"
        assert config.input_sample_rate == 16000
        assert config.output_sample_rate == 24000


class TestAppConfig:
    def test_defaults(self):
        config = AppConfig()
        assert config.log_level == "INFO"
        assert config.default_provider == "google"
        assert config.default_agent == "english_teacher"
        assert config.port == 8000

    def test_nested_configs(self):
        config = AppConfig()
        assert isinstance(config.google, GoogleProviderConfig)
        assert isinstance(config.bedrock, BedrockProviderConfig)
