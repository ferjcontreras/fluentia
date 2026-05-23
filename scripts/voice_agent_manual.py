"""Voice Agent (Manual Wiring) - Low-level example showing component integration.

This script demonstrates how to manually wire together SpeechCaller and AudioStreamer,
following the same patterns as the AWS reference implementation. Use this as a reference
for understanding how the components work together, or when you need more control.

For most use cases, prefer the simpler voice_agent.py which uses the VoiceAgent class.

Usage:
    python scripts/voice_agent_manual.py [--debug] [--region REGION] [--voice VOICE]

Requirements:
    - AWS credentials configured (environment variables or ~/.aws/credentials)
    - Microphone and speakers connected
    - PortAudio installed (apt-get install portaudio19-dev on Ubuntu)
"""

import argparse
import asyncio
import logging
import sys

from livoia.audio import AudioConfig
from livoia.audio import AudioStreamer
from livoia.clients.speech import BedrockSonicClientConfig
from livoia.clients.speech import SpeechEvents
from livoia.modules import BedrockSonicProviderConfig
from livoia.modules import SpeechCaller
from livoia.modules import SpeechCallerConfig
from livoia.tools import BaseTool
from livoia.tools.implementations.date_time import GetDateAndTimeTool

logger: logging.Logger = logging.getLogger(__name__)

# Default system prompt matching reference implementation
DEFAULT_SYSTEM_PROMPT: str = (
    "You are a warm, professional, and helpful male AI assistant. "
    "Give accurate answers that sound natural, direct, and human. "
    "Start by answering the user's question clearly in 1-2 sentences. "
    "Then, expand only enough to make the answer understandable, "
    "staying within 3-5 short sentences total. "
    "Avoid sounding like a lecture or essay."
)


async def process_speech_events(speech_caller: SpeechCaller, audio_streamer: AudioStreamer) -> None:
    """Process events from the speech caller in a background task.

    This coroutine handles the event loop that:
    - Receives audio output and queues it for playback
    - Displays text transcriptions (user and assistant)
    - Detects and handles barge-in (user interrupting assistant)

    Args:
        speech_caller: The speech caller to receive events from.
        audio_streamer: The audio streamer to play audio through.
    """
    logger.debug("Starting event processing loop")

    try:
        async for event in speech_caller.receive_events():
            # Handle audio output - queue for playback
            if isinstance(event, SpeechEvents.AudioOutput):
                # Check for barge-in before queueing more audio
                if speech_caller.barge_in_detected:
                    logger.debug("Barge-in detected, triggering audio clear")
                    audio_streamer.trigger_barge_in()
                    speech_caller.clear_barge_in()
                else:
                    await audio_streamer.play_audio(event.audio_bytes)

            # Handle text output - display transcriptions
            elif isinstance(event, SpeechEvents.TextOutput):
                if event.role == "USER":
                    logger.info("User: %s", event.content)
                elif event.role == "ASSISTANT":
                    logger.info("Assistant: %s", event.content)

            # Handle content end
            elif isinstance(event, SpeechEvents.ContentEnd):
                logger.debug("Content ended: %s", event.content_type)

    except asyncio.CancelledError:
        logger.debug("Event processing cancelled")
    except Exception as e:
        logger.exception("Error processing speech events: %s", e)


async def run_voice_agent(region: str, voice_id: str, system_prompt: str) -> None:
    """Run the voice agent until user presses Enter.

    This is the main orchestration function that:
    1. Creates and configures the speech caller with tools
    2. Creates and configures the audio streamer
    3. Connects to Nova Sonic and starts streaming
    4. Waits for user to press Enter to stop

    Args:
        region: AWS region for Bedrock.
        voice_id: Voice ID for speech synthesis.
        system_prompt: System prompt for the conversation.
    """
    speech_caller: SpeechCaller | None = None
    audio_streamer: AudioStreamer | None = None
    event_task: asyncio.Task[None] | None = None

    try:
        # Create speech caller configuration
        logger.debug("Creating speech caller configuration")
        client_config: BedrockSonicClientConfig = BedrockSonicClientConfig(
            region=region,
            model_id="amazon.nova-2-sonic-v1:0",
            voice_id=voice_id,
            input_sample_rate=16000,
            output_sample_rate=24000,
        )

        provider_config: BedrockSonicProviderConfig = BedrockSonicProviderConfig(
            provider="bedrock_sonic", provider_config=client_config
        )

        caller_config: SpeechCallerConfig = SpeechCallerConfig(
            provider_settings=provider_config, system_prompt=system_prompt
        )

        # Create tools
        tools: list[BaseTool] = [GetDateAndTimeTool()]

        # Create speech caller
        logger.debug("Creating speech caller")
        speech_caller = SpeechCaller(config=caller_config, tools=tools)

        # Create audio input callback
        async def on_audio_input(audio_bytes: bytes) -> None:
            """Send microphone audio to the speech caller."""
            if speech_caller and speech_caller.is_active:
                await speech_caller.send_audio(audio_bytes)

        # Create audio streamer
        logger.debug("Creating audio streamer")
        audio_config: AudioConfig = AudioConfig(channels=1, sample_size_bits=16, chunk_size=1024)

        audio_streamer = AudioStreamer(
            config=audio_config,
            input_sample_rate=speech_caller.input_sample_rate,
            output_sample_rate=speech_caller.output_sample_rate,
            on_audio_input=on_audio_input,
        )

        # Connect to Nova Sonic
        logger.debug("Connecting to Bedrock Nova Sonic")
        await speech_caller.connect()

        # Start audio streaming (microphone capture and speaker playback)
        logger.debug("Starting audio streaming")
        await audio_streamer.start()

        # Signal start of audio content to Nova Sonic
        logger.debug("Sending audio content start")
        await speech_caller.start_audio()

        # Start background event processing
        event_task = asyncio.create_task(process_speech_events(speech_caller, audio_streamer))

        # Ready message
        logger.info("Voice agent ready! Speak into your microphone...")
        logger.info("Press Enter to stop.")

        # Wait for user to press Enter
        await asyncio.get_event_loop().run_in_executor(None, input)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")

    finally:
        # Cleanup
        logger.info("Stopping voice agent...")

        # Cancel event processing task
        if event_task and not event_task.done():
            event_task.cancel()
            try:
                await event_task
            except asyncio.CancelledError:
                pass

        # Stop audio streamer
        if audio_streamer:
            logger.debug("Stopping audio streamer")
            await audio_streamer.stop()

        # Stop speech caller
        if speech_caller:
            logger.debug("Sending audio content end")
            try:
                await speech_caller.stop_audio()
            except Exception as e:
                logger.debug("Error stopping audio: %s", e)

            logger.debug("Closing speech caller")
            await speech_caller.close()

        logger.info("Voice agent stopped.")


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

    # Run the voice agent
    await run_voice_agent(
        region=args.region,
        voice_id=args.voice,
        system_prompt=args.system_prompt or DEFAULT_SYSTEM_PROMPT,
    )


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
  python scripts/voice_agent_manual.py
  python scripts/voice_agent_manual.py --debug
  python scripts/voice_agent_manual.py --region us-west-2 --voice ruth

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
        "--system-prompt", type=str, default=None, help="Custom system prompt for the conversation"
    )

    return parser.parse_args()


if __name__ == "__main__":
    parsed_args: argparse.Namespace = parse_args()

    try:
        asyncio.run(main(parsed_args))
    except Exception as e:
        logger.exception("Application error: %s", e)
        sys.exit(1)
