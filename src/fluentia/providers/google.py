"""Google ADK (Gemini) voice provider."""

# pylint: disable=duplicate-code

import asyncio
import base64
import json
import logging
import os
import re
import warnings
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any

from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from google.adk.agents import Agent
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig
from google.adk.agents.run_config import StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from fluentia.config import GoogleModelSpec
from fluentia.config import GoogleProviderConfig
from fluentia.config import get_model_spec
from fluentia.providers.base import BaseProvider
from fluentia.providers.base import SessionContext
from fluentia.providers.google_tools import create_adk_tool_wrapper
from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType
from fluentia.tools.base import BaseTool
from fluentia.tools.processor import ToolProcessor

# Suppress Pydantic serialization warnings from Google ADK
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

logger: logging.Logger = logging.getLogger(__name__)

APP_NAME: str = "fluentia"


class GoogleProvider(BaseProvider):
    """Google ADK (Gemini) voice provider."""

    def __init__(
        self, provider_config: GoogleProviderConfig, tool_processor: ToolProcessor
    ) -> None:
        """Initialize the Google provider."""
        self._config: GoogleProviderConfig = provider_config
        self._tool_processor: ToolProcessor = tool_processor
        self._session_service: InMemorySessionService = InMemorySessionService()

    def _build_run_config(self, websocket: WebSocket, spec: GoogleModelSpec) -> RunConfig:
        """Build an ADK RunConfig from query params and model capabilities."""
        query_params: dict[str, str] = dict(websocket.query_params)
        proactivity: bool = query_params.get("proactivity", "").lower() == "true"
        affective_dialog: bool = query_params.get("affective_dialog", "").lower() == "true"

        if spec.supports_native_audio:
            return RunConfig(
                streaming_mode=StreamingMode.BIDI,
                response_modalities=["AUDIO"],
                input_audio_transcription=types.AudioTranscriptionConfig(),
                output_audio_transcription=types.AudioTranscriptionConfig(),
                session_resumption=types.SessionResumptionConfig(),
                proactivity=(
                    types.ProactivityConfig(proactive_audio=True)
                    if proactivity and spec.supports_proactivity
                    else None
                ),
                enable_affective_dialog=(
                    affective_dialog
                    if affective_dialog and spec.supports_affective_dialog
                    else None
                ),
            )

        if proactivity or affective_dialog:
            logger.warning("Proactivity and affective dialog only supported on native audio models")
        return RunConfig(
            streaming_mode=StreamingMode.BIDI,
            response_modalities=["TEXT"],
            session_resumption=types.SessionResumptionConfig(),
        )

    def _build_adk_tools(
        self, enabled_tools: list[str], emit: Callable[[SessionEvent], Awaitable[None]]
    ) -> list[Any]:
        """Build ADK-compatible tool wrappers from enabled Fluentia tools."""
        adk_tools: list[Any] = []
        for tool_name in enabled_tools:
            if tool_name == "google_search":
                continue  # Handled separately (ADK built-in)
            tool: BaseTool | None = self._tool_processor.get_tool(tool_name)
            if tool:
                wrapper: Callable[..., Awaitable[dict[str, Any]]] = create_adk_tool_wrapper(
                    tool, emit
                )
                adk_tools.append(wrapper)
            else:
                logger.warning("Tool not found for Google ADK: %s", tool_name)
        return adk_tools

    async def _create_runner(
        self, websocket: WebSocket, session_context: SessionContext
    ) -> tuple[Runner, RunConfig, str, str]:
        """Create an ADK Runner with the resolved model, tools, and session."""
        query_params: dict[str, str] = dict(websocket.query_params)
        effective_model: str = query_params.get("model", self._config.model_name)
        effective_spec: GoogleModelSpec = get_model_spec(effective_model)
        logger.info("Google session using model: %s", effective_model)

        raw_prompt: str = session_context.agent_definition.render_prompt()
        # Google ADK interprets {word} in the instruction as context variable
        # placeholders and raises KeyError if the variable is not in the session
        # context. Replace single-brace patterns with square brackets so the ADK
        # treats them as plain text while the agent still sees the meaningful content.
        prompt: str = re.sub(r"\{([^{}]*)\}", r"[\1]", raw_prompt)
        run_config: RunConfig = self._build_run_config(websocket, effective_spec)

        enabled_tools: list[str] = session_context.agent_definition.enabled_tools
        adk_tools: list[Any]
        if effective_spec.supports_tools:
            adk_tools = self._build_adk_tools(enabled_tools, session_context.emit)
        else:
            logger.info(
                "Model %s does not support tools; skipping tool registration", effective_model
            )
            adk_tools = []

        if effective_spec.supports_tools and "google_search" in enabled_tools:
            from google.adk.tools import google_search  # type: ignore[attr-defined]  # pylint: disable=import-outside-toplevel  # noqa: I001

            adk_tools.append(google_search)

        # Set API key in environment for Google SDK
        if self._config.api_key:
            logger.info(
                "Setting GOOGLE_API_KEY from config (length: %d)", len(self._config.api_key)
            )
            os.environ["GOOGLE_API_KEY"] = self._config.api_key
        else:
            logger.warning("No API key found in config!")

        agent: Agent = Agent(
            name="voice_agent", model=effective_model, tools=adk_tools, instruction=prompt
        )
        runner: Runner = Runner(
            app_name=APP_NAME, agent=agent, session_service=self._session_service
        )

        user_id: str = session_context.user_id
        session_id: str = session_context.session_id
        session = await self._session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
        if not session:
            await self._session_service.create_session(
                app_name=APP_NAME, user_id=user_id, session_id=session_id
            )

        return runner, run_config, user_id, session_id

    async def handle_session(self, websocket: WebSocket, session_context: SessionContext) -> None:
        """Run a complete Google ADK voice session."""
        runner, run_config, user_id, session_id = await self._create_runner(
            websocket, session_context
        )
        live_request_queue: LiveRequestQueue = LiveRequestQueue()

        try:

            async def upstream() -> None:
                """Receive messages from WebSocket and forward to ADK."""
                try:
                    while True:
                        message = await websocket.receive()
                        if "bytes" in message:
                            audio_blob: types.Blob = types.Blob(
                                mime_type="audio/pcm;rate=16000", data=message["bytes"]
                            )
                            live_request_queue.send_realtime(audio_blob)
                        elif "text" in message:
                            try:
                                json_msg: dict[str, Any] = json.loads(message["text"])
                                if json_msg.get("type") == "text":
                                    content: types.Content = types.Content(
                                        parts=[types.Part(text=json_msg["text"])]
                                    )
                                    live_request_queue.send_content(content)
                            except json.JSONDecodeError:
                                pass
                except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
                    pass

            async def downstream() -> None:
                """Receive events from ADK and emit as SessionEvents."""
                try:
                    async for adk_event in runner.run_live(
                        user_id=user_id,
                        session_id=session_id,
                        live_request_queue=live_request_queue,
                        run_config=run_config,
                    ):
                        events: list[SessionEvent] = self._convert_adk_event(adk_event)
                        for event in events:
                            await session_context.emit(event)
                except (WebSocketDisconnect, RuntimeError, asyncio.CancelledError):
                    pass

            await asyncio.gather(upstream(), downstream())

        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception:
            logger.exception("Error in Google session %s", session_id)
            await session_context.emit(
                SessionEvent(
                    type=SessionEventType.ERROR,
                    payload={
                        "code": "provider_error",
                        "message": "Google session error",
                        "recoverable": False,
                    },
                )
            )
        finally:
            live_request_queue.close()
            logger.info("Google session ended: %s", session_id)

    def _convert_adk_event(self, adk_event: Any) -> list[SessionEvent]:
        """Convert a Google ADK event to normalized SessionEvents."""
        events: list[SessionEvent] = []
        event_dict: dict[str, Any] = adk_event.model_dump(exclude_none=True, by_alias=True)

        # Handle turn complete
        if event_dict.get("turnComplete"):
            events.append(SessionEvent(type=SessionEventType.TURN_COMPLETE))
            return events

        # Handle interrupted
        if event_dict.get("interrupted"):
            events.append(SessionEvent(type=SessionEventType.INTERRUPTED))
            return events

        # Handle input transcription
        if "inputTranscription" in event_dict:
            transcription: dict[str, Any] = event_dict["inputTranscription"]
            if transcription.get("text"):
                events.append(
                    SessionEvent(
                        type=SessionEventType.INPUT_TRANSCRIPTION,
                        payload={
                            "text": transcription["text"],
                            "is_partial": not transcription.get("finished", False),
                        },
                    )
                )

        # Handle output transcription
        if "outputTranscription" in event_dict:
            transcription = event_dict["outputTranscription"]
            if transcription.get("text"):
                events.append(
                    SessionEvent(
                        type=SessionEventType.OUTPUT_TRANSCRIPTION,
                        payload={
                            "text": transcription["text"],
                            "is_partial": not transcription.get("finished", False),
                        },
                    )
                )

        # Handle content (audio/text)
        if "content" in event_dict and "parts" in event_dict["content"]:
            parts: list[dict[str, Any]] = event_dict["content"]["parts"]
            for part in parts:
                if "inlineData" in part:
                    inline: dict[str, Any] = part["inlineData"]
                    mime_type: str = inline.get("mimeType", "")
                    if mime_type.startswith("audio/pcm"):
                        raw_data: Any = inline.get("data", b"")
                        encoded: str = (
                            base64.b64encode(raw_data).decode("ascii")
                            if isinstance(raw_data, bytes)
                            else str(raw_data)
                        )
                        events.append(
                            SessionEvent(
                                type=SessionEventType.AUDIO,
                                payload={
                                    "data": encoded,
                                    "sample_rate": self._extract_sample_rate(mime_type),
                                },
                            )
                        )
                if "text" in part:
                    events.append(
                        SessionEvent(type=SessionEventType.TEXT, payload={"content": part["text"]})
                    )

        return events

    @staticmethod
    def _extract_sample_rate(mime_type: str) -> int:
        """Extract sample rate from MIME type like 'audio/pcm;rate=24000'."""
        if "rate=" in mime_type:
            try:
                rate_str: str = mime_type.split("rate=")[1].split(";")[0]
                return int(rate_str)
            except (IndexError, ValueError):
                pass
        return 24000
