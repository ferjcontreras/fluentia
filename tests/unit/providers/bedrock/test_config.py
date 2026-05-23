"""Tests for Bedrock session configuration."""

import pytest
from pydantic import ValidationError

from fluentia.providers.bedrock.config import BedrockSessionConfig


class TestBedrockSessionConfig:
    """Tests for BedrockSessionConfig Pydantic model."""

    def test_defaults(self):
        """Test default configuration values."""
        config: BedrockSessionConfig = BedrockSessionConfig()
        assert config.region == "us-east-1"
        assert config.model_id == "amazon.nova-2-sonic-v1:0"
        assert config.voice_id == "matthew"
        assert config.input_sample_rate == 16000
        assert config.output_sample_rate == 24000
        assert config.language is None
        assert config.max_tokens == 1024
        assert config.temperature == 0.7
        assert config.top_p == 0.9

    def test_custom_values(self):
        """Test creating config with custom values."""
        config: BedrockSessionConfig = BedrockSessionConfig(
            region="eu-west-1",
            voice_id="tiffany",
            language="en-US",
            max_tokens=512,
            temperature=0.5,
            top_p=0.8,
        )
        assert config.region == "eu-west-1"
        assert config.voice_id == "tiffany"
        assert config.language == "en-US"
        assert config.max_tokens == 512
        assert config.temperature == 0.5
        assert config.top_p == 0.8

    def test_temperature_validation_too_high(self):
        """Test that temperature > 1.0 raises validation error."""
        with pytest.raises(ValidationError):
            BedrockSessionConfig(temperature=1.5)

    def test_temperature_validation_too_low(self):
        """Test that temperature < 0.0 raises validation error."""
        with pytest.raises(ValidationError):
            BedrockSessionConfig(temperature=-0.1)

    def test_top_p_validation(self):
        """Test that top_p > 1.0 raises validation error."""
        with pytest.raises(ValidationError):
            BedrockSessionConfig(top_p=1.5)

    def test_max_tokens_must_be_positive(self):
        """Test that max_tokens must be > 0."""
        with pytest.raises(ValidationError):
            BedrockSessionConfig(max_tokens=0)
