"""Bedrock-specific configuration."""

from pydantic import BaseModel
from pydantic import Field


class BedrockSessionConfig(BaseModel):
    """Configuration for a single Bedrock Nova Sonic session."""

    region: str = Field(default="us-east-1", description="AWS region")
    model_id: str = Field(default="amazon.nova-2-sonic-v1:0", description="Nova Sonic model ID")
    voice_id: str = Field(default="matthew", description="Voice for speech synthesis")
    input_sample_rate: int = Field(default=16000, description="Input sample rate in Hz")
    output_sample_rate: int = Field(default=24000, description="Output sample rate in Hz")
    language: str | None = Field(default=None, description="Language code (e.g., 'en-US')")
    max_tokens: int = Field(default=1024, gt=0, description="Max tokens in response")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling parameter")
