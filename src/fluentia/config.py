"""Application configuration using Pydantic BaseSettings."""

# pylint: disable=no-member  # Pydantic fields are not recognized by pylint

from pydantic import BaseModel
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class GoogleModelSpec(BaseModel, frozen=True):
    """Capabilities and metadata for a known Google Gemini model."""

    model_id: str
    display_name: str
    supports_native_audio: bool = Field(default=True, description="Model supports native audio I/O")
    supports_proactivity: bool = Field(default=False, description="Model supports proactive audio")
    supports_affective_dialog: bool = Field(
        default=False, description="Model supports affective dialog"
    )
    supports_tools: bool = Field(
        default=True, description="Model supports async function calling (tools)"
    )
    is_default: bool = Field(default=False, description="Whether this is the default model")


GOOGLE_MODEL_CATALOG: dict[str, GoogleModelSpec] = {
    "gemini-2.5-flash-native-audio-preview-12-2025": GoogleModelSpec(
        model_id="gemini-2.5-flash-native-audio-preview-12-2025",
        display_name="Gemini 2.5 Flash Native Audio",
        supports_native_audio=True,
        supports_proactivity=True,
        supports_affective_dialog=True,
        supports_tools=False,  # Native audio doesn't support tools
        is_default=True,
    ),
    "gemini-2.0-flash-exp": GoogleModelSpec(
        model_id="gemini-2.0-flash-exp",
        display_name="Gemini 2.0 Flash (with tools)",
        supports_native_audio=False,
        supports_proactivity=False,
        supports_affective_dialog=False,
        supports_tools=True,
        is_default=False,
    ),
    "gemini-3.1-flash-live-preview": GoogleModelSpec(
        model_id="gemini-3.1-flash-live-preview",
        display_name="Gemini 3.1 Flash Live",
        supports_native_audio=True,
        supports_proactivity=False,
        supports_affective_dialog=False,
        supports_tools=False,
    ),
}

DEFAULT_GOOGLE_MODEL: str = next(
    (spec.model_id for spec in GOOGLE_MODEL_CATALOG.values() if spec.is_default),
    "gemini-2.5-flash-native-audio-preview-12-2025",
)


def get_model_spec(model_name: str) -> GoogleModelSpec:
    """Look up a model spec from the catalog, with a fallback for unknown models."""
    return GOOGLE_MODEL_CATALOG.get(
        model_name,
        GoogleModelSpec(
            model_id=model_name,
            display_name=model_name,
            supports_native_audio="native-audio" in model_name.lower(),
        ),
    )


class GoogleProviderConfig(BaseSettings):
    """Google ADK provider configuration."""

    model_config = SettingsConfigDict(
        env_prefix="GOOGLE_",
        populate_by_name=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(default="", description="Google API key (Gemini API)")
    cloud_project: str = Field(default="", description="Google Cloud project (Vertex AI)")
    model_name: str = Field(
        default=DEFAULT_GOOGLE_MODEL, description="Gemini model ID", validation_alias="GOOGLE_MODEL"
    )

    @property
    def model_spec(self) -> GoogleModelSpec:
        """Look up the model spec from the catalog."""
        return get_model_spec(self.model_name)

    @property
    def is_native_audio(self) -> bool:
        """Check if the model supports native audio."""
        return self.model_spec.supports_native_audio


class BedrockProviderConfig(BaseSettings):
    """AWS Bedrock Nova Sonic provider configuration."""

    model_config = SettingsConfigDict(env_prefix="BEDROCK_")

    region: str = Field(default="us-east-1", description="AWS region")
    model_id: str = Field(default="amazon.nova-2-sonic-v1:0", description="Nova Sonic model ID")
    voice_id: str = Field(default="matthew", description="Voice for speech synthesis")
    input_sample_rate: int = Field(default=16000, description="Input audio sample rate in Hz")
    output_sample_rate: int = Field(default=24000, description="Output audio sample rate in Hz")
    language: str | None = Field(
        default=None,
        description="Language code for input audio (e.g., 'en-US'). None for auto-detect.",
    )


class AppConfig(BaseSettings):
    """Root application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="FLUENTIA_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="0.0.0.0", description="Server bind address")  # noqa: S104
    port: int = Field(default=8000, description="Server port")
    log_level: str = Field(default="INFO", description="Log level")
    default_provider: str = Field(default="google", description="Default voice provider")
    default_agent: str = Field(default="english_teacher", description="Default agent definition")

    google: GoogleProviderConfig = Field(default_factory=GoogleProviderConfig)
    bedrock: BedrockProviderConfig = Field(default_factory=BedrockProviderConfig)
