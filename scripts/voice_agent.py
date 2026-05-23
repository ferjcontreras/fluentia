"""Voice Agent - Real-time speech conversation using the high-level VoiceAgent API.

This is the recommended way to create voice conversations. The VoiceAgent class
handles all the complexity of wiring components together internally.

Usage:
    python scripts/voice_agent.py [--debug] [--region REGION] [--voice VOICE]

Requirements:
    - AWS credentials configured (environment variables or ~/.aws/credentials)
    - Microphone and speakers connected
    - PortAudio installed (apt-get install portaudio19-dev on Ubuntu)
"""

import argparse
import asyncio
import logging
import sys

from livoia.agent import VoiceAgent
from livoia.agent import VoiceAgentConfig
from livoia.tools.implementations.date_time import GetDateAndTimeTool

logger: logging.Logger = logging.getLogger(__name__)

# Default system prompt
DEFAULT_SYSTEM_PROMPT: str = (
    "You are a warm, professional, and helpful male AI assistant. "
    "Give accurate answers that sound natural, direct, and human. "
    "Start by answering the user's question clearly in 1-2 sentences. "
    "Then, expand only enough to make the answer understandable, "
    "staying within 3-5 short sentences total. "
    "Avoid sounding like a lecture or essay."
)


def log_transcription(role: str, text: str) -> None:
    """Log transcription from the voice agent.

    Args:
        role: The speaker role (USER or ASSISTANT).
        text: The transcribed text.
    """
    logger.info("%s: %s", role, text)


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

    # Create configuration
    config: VoiceAgentConfig = VoiceAgentConfig(
        region=args.region,
        voice_id=args.voice,
        language=args.language,
        system_prompt=args.system_prompt or DEFAULT_SYSTEM_PROMPT,
    )

    # Create agent with tools
    agent: VoiceAgent = VoiceAgent(config, tools=[GetDateAndTimeTool()])

    # Register transcription callback
    agent.on_transcription(log_transcription)

    # Run the agent
    logger.info("Voice agent ready! Speak into your microphone...")
    logger.info("Press Enter to stop.")

    await agent.run()

    logger.info("Goodbye!")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Simple Voice Agent Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/voice_agent.py
  python scripts/voice_agent.py --debug
  python scripts/voice_agent.py --region us-west-2 --voice ruth
  python scripts/voice_agent.py --language en-US

Available voices: matthew, ruth, amy, gregory
Common language codes: en-US, en-GB, es-ES, es-US, fr-FR, de-DE, it-IT, pt-BR
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
        "--language",
        type=str,
        default=None,
        help="Language code for input audio (e.g., 'en-US', 'es-ES'). Default: auto-detect",
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
