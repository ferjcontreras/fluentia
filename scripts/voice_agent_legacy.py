"""Voice Agent (Legacy) - Original class-based implementation.

This was an intermediate implementation that wrapped components in a VoiceAgentDemo class.
It has been superseded by:
- voice_agent.py - Simple, recommended approach using VoiceAgent
- voice_agent_manual.py - Low-level approach for more control

Kept for historical reference only.

Usage:
    python scripts/voice_agent_legacy.py [--debug] [--region REGION] [--voice VOICE]

Requirements:
    - AWS credentials configured (environment variables or ~/.aws/credentials)
    - Microphone and speakers connected
    - PortAudio installed (apt-get install portaudio19-dev on Ubuntu)
"""

import argparse
import asyncio
import logging
import sys
from typing import Any

from livoia.audio import AudioConfig
from livoia.audio import AudioStreamer
from livoia.clients.speech import BedrockSonicClientConfig
from livoia.clients.speech import SpeechEvents
from livoia.modules import BedrockSonicProviderConfig
from livoia.modules import SpeechCaller
from livoia.modules import SpeechCallerConfig
from livoia.tools.implementations.date_time import GetDateAndTimeTool

logger: logging.Logger = logging.getLogger(__name__)


class VoiceAgentDemo:
    """Demonstration voice agent that handles speech-to-speech conversations.

    This class orchestrates the SpeechCaller and AudioStreamer to provide
    a complete voice conversation experience with tool support.
    """

    def __init__(
        self, region: str = "us-east-1", voice_id: str = "matthew", system_prompt: str | None = None
    ) -> None:
        """Initialize the voice agent demo.

        Args:
            region: AWS region for Bedrock (default: us-east-1).
            voice_id: Voice ID for speech synthesis (default: matthew).
            system_prompt: Custom system prompt (default: helpful assistant prompt).
        """
        self._region: str = region
        self._voice_id: str = voice_id
        self._system_prompt: str = system_prompt or self._default_system_prompt()

        # Components (initialized in start())
        self._speech_caller: SpeechCaller | None = None
        self._audio_streamer: AudioStreamer | None = None
        self._event_task: asyncio.Task[None] | None = None

        # State tracking
        self._is_running: bool = False

    @staticmethod
    def _default_system_prompt() -> str:
        """Get the default system prompt.

        Returns:
            Default system prompt for the voice agent.
        """
        return (
            "You are a warm, professional, and helpful male AI assistant. "
            "Give accurate answers that sound natural, direct, and human. "
            "Start by answering the user's question clearly in 1-2 sentences. "
            "Then, expand only enough to make the answer understandable, "
            "staying within 3-5 short sentences total. "
            "Avoid sounding like a lecture or essay."
        )

    def _create_speech_caller(self) -> SpeechCaller:
        """Create and configure the speech caller.

        Returns:
            Configured SpeechCaller instance.
        """
        # Configure the Bedrock Sonic client
        client_config: BedrockSonicClientConfig = BedrockSonicClientConfig(
            region=self._region,
            model_id="amazon.nova-2-sonic-v1:0",
            voice_id=self._voice_id,
            input_sample_rate=16000,
            output_sample_rate=24000,
        )

        # Create provider config
        provider_config: BedrockSonicProviderConfig = BedrockSonicProviderConfig(
            provider="bedrock_sonic", provider_config=client_config
        )

        # Create speech caller config
        config: SpeechCallerConfig = SpeechCallerConfig(
            provider_settings=provider_config, system_prompt=self._system_prompt
        )

        # Create speech caller with tools
        tools: list[Any] = [GetDateAndTimeTool()]

        return SpeechCaller(config=config, tools=tools)

    def _create_audio_streamer(self) -> AudioStreamer:
        """Create and configure the audio streamer.

        Returns:
            Configured AudioStreamer instance.
        """
        if self._speech_caller is None:
            raise RuntimeError("SpeechCaller must be created before AudioStreamer")

        audio_config: AudioConfig = AudioConfig(channels=1, sample_size_bits=16, chunk_size=1024)

        return AudioStreamer(
            config=audio_config,
            input_sample_rate=self._speech_caller.input_sample_rate,
            output_sample_rate=self._speech_caller.output_sample_rate,
            on_audio_input=self._handle_audio_input,
        )

    async def _handle_audio_input(self, audio_bytes: bytes) -> None:
        """Handle audio input from the microphone.

        Args:
            audio_bytes: Raw audio bytes from the microphone.
        """
        if self._speech_caller and self._speech_caller.is_active:
            await self._speech_caller.send_audio(audio_bytes)

    async def _process_events(self) -> None:
        """Process events from the speech caller.

        This method runs in the background, handling audio output
        and displaying transcriptions.
        """
        if self._speech_caller is None or self._audio_streamer is None:
            return

        try:
            async for event in self._speech_caller.receive_events():
                if isinstance(event, SpeechEvents.AudioOutput):
                    # Check for barge-in
                    if self._speech_caller.barge_in_detected:
                        logger.debug("Barge-in detected, clearing audio output")
                        self._audio_streamer.trigger_barge_in()
                        self._speech_caller.clear_barge_in()
                    else:
                        # Play audio output
                        await self._audio_streamer.play_audio(event.audio_bytes)

                elif isinstance(event, SpeechEvents.TextOutput):
                    # Display transcription
                    if event.role == "USER":
                        logger.info("User: %s", event.content)
                    elif event.role == "ASSISTANT":
                        logger.info("Assistant: %s", event.content)

                elif isinstance(event, SpeechEvents.ContentEnd):
                    logger.debug("Content ended: %s", event.content_type)

        except asyncio.CancelledError:
            logger.debug("Event processing cancelled")
        except Exception as e:
            logger.exception("Error processing events: %s", e)

    async def start(self) -> None:
        """Start the voice agent.

        This method initializes all components and begins the conversation.
        """
        if self._is_running:
            logger.warning("Voice agent is already running")
            return

        logger.info("Initializing voice agent...")
        logger.debug("Creating speech caller")

        # Create components
        self._speech_caller = self._create_speech_caller()
        self._audio_streamer = self._create_audio_streamer()

        # Connect to the speech service
        logger.debug("Connecting to Bedrock Nova Sonic")
        await self._speech_caller.connect()

        # Start audio streaming
        logger.debug("Starting audio streaming")
        await self._audio_streamer.start()

        # Signal start of audio content
        await self._speech_caller.start_audio()

        # Start event processing
        self._event_task = asyncio.create_task(self._process_events())

        self._is_running = True
        logger.info("Voice agent ready! Speak into your microphone...")
        logger.info("Press Enter to stop.")

    async def stop(self) -> None:
        """Stop the voice agent and clean up resources."""
        if not self._is_running:
            return

        logger.info("Stopping voice agent...")
        self._is_running = False

        # Cancel event processing
        if self._event_task and not self._event_task.done():
            self._event_task.cancel()
            try:
                await self._event_task
            except asyncio.CancelledError:
                pass

        # Stop audio streaming
        if self._audio_streamer:
            logger.debug("Stopping audio streamer")
            await self._audio_streamer.stop()

        # Stop speech caller
        if self._speech_caller:
            logger.debug("Stopping audio content")
            try:
                await self._speech_caller.stop_audio()
            except Exception as e:
                logger.debug("Error stopping audio: %s", e)

            logger.debug("Closing speech caller")
            await self._speech_caller.close()

        logger.info("Voice agent stopped.")

    async def run(self) -> None:
        """Run the voice agent until user presses Enter."""
        try:
            await self.start()

            # Wait for user to press Enter
            await asyncio.get_event_loop().run_in_executor(None, input)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        finally:
            await self.stop()


async def main(args: argparse.Namespace) -> None:
    """Main entry point.

    Args:
        args: Parsed command-line arguments.
    """
    # Configure logging - use INFO level to see transcriptions
    log_level: int = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create and run the voice agent
    agent: VoiceAgentDemo = VoiceAgentDemo(
        region=args.region, voice_id=args.voice, system_prompt=args.system_prompt
    )

    await agent.run()


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Voice Agent Demo - Real-time speech-to-speech conversation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/voice_agent_legacy.py
  python scripts/voice_agent_legacy.py --debug
  python scripts/voice_agent_legacy.py --region us-west-2 --voice ruth

Available voices: matthew, ruth, amy, gregory
        """,
    )

    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode with verbose output"
    )

    parser.add_argument(
        "--region",
        type=str,
        default="us-east-1",
        help="AWS region for Bedrock (default: us-east-1)",
    )

    parser.add_argument(
        "--voice",
        type=str,
        default="matthew",
        choices=["matthew", "ruth", "amy", "gregory"],
        help="Voice ID for speech synthesis (default: matthew)",
    )

    parser.add_argument(
        "--system-prompt", type=str, default=None, help="Custom system prompt for the voice agent"
    )

    return parser.parse_args()


if __name__ == "__main__":
    parsed_args: argparse.Namespace = parse_args()

    try:
        asyncio.run(main(parsed_args))
    except Exception as e:
        logger.exception("Application error: %s", e)
        sys.exit(1)
