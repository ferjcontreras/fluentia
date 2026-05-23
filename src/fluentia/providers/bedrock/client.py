"""Low-level Nova Sonic streaming client.

Ported from the PoC's bedrock_sonic.py with simplified interface.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Any

from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient
from aws_sdk_bedrock_runtime.client import InvokeModelWithBidirectionalStreamOperationInput
from aws_sdk_bedrock_runtime.config import Config
from aws_sdk_bedrock_runtime.models import BidirectionalInputPayloadPart
from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk

from fluentia.providers.bedrock.auth import create_bedrock_config
from fluentia.providers.bedrock.config import BedrockSessionConfig
from fluentia.session.events import SessionEvent
from fluentia.session.events import SessionEventType

logger: logging.Logger = logging.getLogger(__name__)


class NovaSonicClient:  # pylint: disable=too-many-instance-attributes
    """Low-level HTTP/2 bidirectional streaming client for Bedrock Nova Sonic.

    Manages connection, audio encoding, event parsing, and tool execution.
    Emits normalized SessionEvent objects.
    """

    def __init__(self, config: BedrockSessionConfig) -> None:
        """Initialize NovaSonicClient."""
        self.config: BedrockSessionConfig = config
        self._bedrock_client: BedrockRuntimeClient | None = None
        self._stream_response: Any = None
        self._is_active: bool = False
        self._barge_in: bool = False

        # Session identifiers
        self._prompt_name: str = str(uuid.uuid4())
        self._content_name: str = str(uuid.uuid4())
        self._audio_content_name: str = str(uuid.uuid4())

        # Async queues
        self._audio_input_queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._event_queue: asyncio.Queue[SessionEvent | _InternalToolUseEvent] = asyncio.Queue()

        # Background tasks
        self._response_task: asyncio.Task[None] | None = None
        self._audio_input_task: asyncio.Task[None] | None = None

        # Tool use state
        self._current_tool_use_id: str = ""
        self._current_tool_name: str = ""
        self._current_tool_content: dict[str, Any] = {}

        # Text output state
        self._current_role: str | None = None
        self._display_assistant_text: bool = False

    @property
    def is_active(self) -> bool:
        """Check if the stream is active."""
        return self._is_active

    @property
    def barge_in_detected(self) -> bool:
        """Check if barge-in was detected."""
        return self._barge_in

    def _initialize_bedrock_client(self) -> None:
        """Initialize the Bedrock runtime client."""
        bedrock_config: Config = create_bedrock_config(self.config.region)
        self._bedrock_client = BedrockRuntimeClient(config=bedrock_config)

    async def connect(self, system_prompt: str, tool_specs: list[dict[str, Any]]) -> None:
        """Initialize the bidirectional stream with Bedrock."""
        if self._bedrock_client is None:
            self._initialize_bedrock_client()

        if self._bedrock_client is None:
            raise RuntimeError("Failed to initialize Bedrock client")

        self._stream_response = await self._bedrock_client.invoke_model_with_bidirectional_stream(
            InvokeModelWithBidirectionalStreamOperationInput(model_id=self.config.model_id)
        )
        self._is_active = True

        # Send initialization events with small delays
        await self._send_session_start_event()
        await asyncio.sleep(0.1)
        await self._send_prompt_start_event(tool_specs)
        await asyncio.sleep(0.1)
        await self._send_system_prompt(system_prompt)
        await asyncio.sleep(0.1)
        await self._send_audio_content_start_event()
        await asyncio.sleep(0.1)

        # Start background tasks
        self._response_task = asyncio.create_task(self._process_responses())
        self._audio_input_task = asyncio.create_task(self._process_audio_input())

        logger.info("Nova Sonic stream initialized")

    async def send_audio(self, audio_bytes: bytes) -> None:
        """Send audio data to Bedrock."""
        if not self._is_active:
            return
        await self._audio_input_queue.put(audio_bytes)

    async def send_tool_result(self, tool_use_id: str, result: dict[str, Any]) -> None:
        """Send tool execution result back to the model."""
        if not self._is_active:
            return
        content_name: str = str(uuid.uuid4())
        await self._send_tool_content_start_event(content_name, tool_use_id)
        await self._send_tool_result_event(content_name, result)
        await self._send_content_end_event(content_name)
        logger.debug("Sent tool result for tool_use_id: %s", tool_use_id)

    async def receive_events(self) -> AsyncIterator[SessionEvent | _InternalToolUseEvent]:
        """Receive events from the model."""
        while self._is_active:
            try:
                event: SessionEvent | _InternalToolUseEvent = await asyncio.wait_for(
                    self._event_queue.get(), timeout=0.1
                )
                yield event
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break

    async def close(self) -> None:
        """Close the stream and clean up resources."""
        if not self._is_active:
            return

        # Stop audio input processing
        if self._audio_input_task and not self._audio_input_task.done():
            self._audio_input_task.cancel()
            try:
                await self._audio_input_task
            except asyncio.CancelledError:
                pass

        # Send closing events
        try:
            await self._send_content_end_event(self._audio_content_name)
            await self._send_prompt_end_event()
            await self._send_session_end_event()
        except Exception:
            logger.debug("Failed to send closing events during shutdown", exc_info=True)

        self._is_active = False

        # Close input stream
        if self._stream_response:
            try:
                await self._stream_response.input_stream.close()
            except Exception:
                logger.debug("Failed to close input stream", exc_info=True)

        # Wait for response task
        if self._response_task and not self._response_task.done():
            done: set[asyncio.Task[None]]
            done, _ = await asyncio.wait({self._response_task}, timeout=2.0)
            if not done:
                self._response_task.cancel()
                try:
                    await self._response_task
                except asyncio.CancelledError:
                    pass

        logger.info("Nova Sonic stream closed")

    # =========================================================================
    # Event Sending Methods
    # =========================================================================

    async def _send_raw_event(self, event_json: str) -> None:
        """Send a raw event JSON to the Bedrock stream."""
        if not self._stream_response or not self._is_active:
            return
        event: InvokeModelWithBidirectionalStreamInputChunk = (
            InvokeModelWithBidirectionalStreamInputChunk(
                value=BidirectionalInputPayloadPart(bytes_=event_json.encode("utf-8"))
            )
        )
        await self._stream_response.input_stream.send(event)

    async def _send_session_start_event(self) -> None:
        """Send session start event."""
        event: dict[str, Any] = {
            "event": {
                "sessionStart": {
                    "inferenceConfiguration": {
                        "maxTokens": self.config.max_tokens,
                        "topP": self.config.top_p,
                        "temperature": self.config.temperature,
                    }
                }
            }
        }
        await self._send_raw_event(json.dumps(event))

    async def _send_prompt_start_event(self, tool_specs: list[dict[str, Any]]) -> None:
        """Send prompt start event with tool configuration."""
        prompt_start: dict[str, Any] = {
            "promptName": self._prompt_name,
            "textOutputConfiguration": {"mediaType": "text/plain"},
            "audioOutputConfiguration": {
                "mediaType": "audio/lpcm",
                "sampleRateHertz": self.config.output_sample_rate,
                "sampleSizeBits": 16,
                "channelCount": 1,
                "voiceId": self.config.voice_id,
                "encoding": "base64",
                "audioType": "SPEECH",
            },
            "toolUseOutputConfiguration": {"mediaType": "application/json"},
        }
        if tool_specs:
            prompt_start["toolConfiguration"] = {"tools": tool_specs}
        await self._send_raw_event(json.dumps({"event": {"promptStart": prompt_start}}))

    async def _send_system_prompt(self, system_prompt: str) -> None:
        """Send system prompt as text content."""
        content_start: dict[str, Any] = {
            "event": {
                "contentStart": {
                    "promptName": self._prompt_name,
                    "contentName": self._content_name,
                    "type": "TEXT",
                    "role": "SYSTEM",
                    "interactive": False,
                    "textInputConfiguration": {"mediaType": "text/plain"},
                }
            }
        }
        await self._send_raw_event(json.dumps(content_start))

        text_input: dict[str, Any] = {
            "event": {
                "textInput": {
                    "promptName": self._prompt_name,
                    "contentName": self._content_name,
                    "content": system_prompt,
                }
            }
        }
        await self._send_raw_event(json.dumps(text_input))
        await self._send_content_end_event(self._content_name)

    async def _send_audio_content_start_event(self) -> None:
        """Send audio content start event."""
        audio_input_config: dict[str, Any] = {
            "mediaType": "audio/lpcm",
            "sampleRateHertz": self.config.input_sample_rate,
            "sampleSizeBits": 16,
            "channelCount": 1,
            "audioType": "SPEECH",
            "encoding": "base64",
        }
        if self.config.language is not None:
            audio_input_config["language"] = self.config.language

        event: dict[str, Any] = {
            "event": {
                "contentStart": {
                    "promptName": self._prompt_name,
                    "contentName": self._audio_content_name,
                    "type": "AUDIO",
                    "interactive": True,
                    "role": "USER",
                    "audioInputConfiguration": audio_input_config,
                }
            }
        }
        await self._send_raw_event(json.dumps(event))

    async def _send_audio_input_event(self, audio_bytes: bytes) -> None:
        """Send audio input event."""
        encoded_audio: str = base64.b64encode(audio_bytes).decode("utf-8")
        event: dict[str, Any] = {
            "event": {
                "audioInput": {
                    "promptName": self._prompt_name,
                    "contentName": self._audio_content_name,
                    "content": encoded_audio,
                }
            }
        }
        await self._send_raw_event(json.dumps(event))

    async def _send_content_end_event(self, content_name: str) -> None:
        """Send content end event."""
        event: dict[str, Any] = {
            "event": {"contentEnd": {"promptName": self._prompt_name, "contentName": content_name}}
        }
        await self._send_raw_event(json.dumps(event))

    async def _send_tool_content_start_event(self, content_name: str, tool_use_id: str) -> None:
        """Send tool content start event."""
        event: dict[str, Any] = {
            "event": {
                "contentStart": {
                    "promptName": self._prompt_name,
                    "contentName": content_name,
                    "interactive": False,
                    "type": "TOOL",
                    "role": "TOOL",
                    "toolResultInputConfiguration": {
                        "toolUseId": tool_use_id,
                        "type": "TEXT",
                        "textInputConfiguration": {"mediaType": "text/plain"},
                    },
                }
            }
        }
        await self._send_raw_event(json.dumps(event))

    async def _send_tool_result_event(self, content_name: str, result: dict[str, Any]) -> None:
        """Send tool result event."""
        event: dict[str, Any] = {
            "event": {
                "toolResult": {
                    "promptName": self._prompt_name,
                    "contentName": content_name,
                    "content": json.dumps(result),
                }
            }
        }
        await self._send_raw_event(json.dumps(event))

    async def _send_prompt_end_event(self) -> None:
        """Send prompt end event."""
        await self._send_raw_event(
            json.dumps({"event": {"promptEnd": {"promptName": self._prompt_name}}})
        )

    async def _send_session_end_event(self) -> None:
        """Send session end event."""
        await self._send_raw_event(json.dumps({"event": {"sessionEnd": {}}}))

    # =========================================================================
    # Background Processing
    # =========================================================================

    async def _process_audio_input(self) -> None:
        """Process audio input from the queue and send to Bedrock."""
        while self._is_active:
            try:
                audio_bytes: bytes = await asyncio.wait_for(
                    self._audio_input_queue.get(), timeout=0.1
                )
                await self._send_audio_input_event(audio_bytes)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error processing audio input: %s", str(e))

    async def _process_responses(self) -> None:
        """Process incoming responses from Bedrock."""
        try:
            while self._is_active:
                try:
                    output: Any = await self._stream_response.await_output()
                    result: Any = await output[1].receive()
                    if result.value and result.value.bytes_:
                        response_data: str = result.value.bytes_.decode("utf-8")
                        await self._handle_response_data(response_data)
                except StopAsyncIteration:
                    break
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    if "ValidationException" in str(e):
                        logger.error("Validation error: %s", str(e))
                    else:
                        logger.error("Error receiving response: %s", str(e))
                    break
        except Exception as e:
            logger.error("Response processing error: %s", str(e))
        finally:
            self._is_active = False

    async def _handle_response_data(self, response_data: str) -> None:
        """Handle a response data string from Bedrock."""
        try:
            json_data: dict[str, Any] = json.loads(response_data)
        except json.JSONDecodeError:
            return

        if "event" not in json_data:
            return

        event_data: dict[str, Any] = json_data["event"]

        if "contentStart" in event_data:
            self._handle_content_start(event_data["contentStart"])
        elif "textOutput" in event_data:
            await self._handle_text_output(event_data["textOutput"])
        elif "audioOutput" in event_data:
            await self._handle_audio_output(event_data["audioOutput"])
        elif "toolUse" in event_data:
            self._handle_tool_use(event_data["toolUse"])
        elif "contentEnd" in event_data:
            await self._handle_content_end(event_data["contentEnd"])

    def _handle_content_start(self, content_start: dict[str, Any]) -> None:
        """Handle content start event."""
        self._current_role = content_start.get("role")
        if "additionalModelFields" in content_start:
            try:
                additional: dict[str, Any] = json.loads(content_start["additionalModelFields"])
                self._display_assistant_text = additional.get("generationStage") == "SPECULATIVE"
            except json.JSONDecodeError:
                self._display_assistant_text = False
        else:
            self._display_assistant_text = False

    async def _handle_text_output(self, text_output: dict[str, Any]) -> None:
        """Handle text output event."""
        content: str = text_output.get("content", "")

        if '{ "interrupted" : true }' in content:
            self._barge_in = True
            await self._event_queue.put(SessionEvent(type=SessionEventType.INTERRUPTED))
            return

        if self._current_role == "USER":
            await self._event_queue.put(
                SessionEvent(
                    type=SessionEventType.INPUT_TRANSCRIPTION,
                    payload={"text": content, "is_partial": False},
                )
            )
        elif self._current_role == "ASSISTANT" and self._display_assistant_text:
            await self._event_queue.put(
                SessionEvent(
                    type=SessionEventType.OUTPUT_TRANSCRIPTION,
                    payload={"text": content, "is_partial": False},
                )
            )

    async def _handle_audio_output(self, audio_output: dict[str, Any]) -> None:
        """Handle audio output event."""
        encoded_content: str = audio_output.get("content", "")
        if encoded_content:
            await self._event_queue.put(
                SessionEvent(
                    type=SessionEventType.AUDIO,
                    payload={
                        "data": encoded_content,
                        "sample_rate": self.config.output_sample_rate,
                    },
                )
            )

    def _handle_tool_use(self, tool_use: dict[str, Any]) -> None:
        """Handle tool use event."""
        self._current_tool_use_id = tool_use.get("toolUseId", "")
        self._current_tool_name = tool_use.get("toolName", "")
        self._current_tool_content = tool_use

    async def _handle_content_end(self, content_end: dict[str, Any]) -> None:
        """Handle content end event."""
        content_type: str | None = content_end.get("type")

        if content_type == "TOOL" and self._current_tool_use_id:
            tool_input: dict[str, Any] = {}
            if "content" in self._current_tool_content:
                try:
                    tool_input = json.loads(self._current_tool_content["content"])
                except (json.JSONDecodeError, TypeError):
                    tool_input = self._current_tool_content.get("content", {})

            await self._event_queue.put(
                _InternalToolUseEvent(
                    tool_use_id=self._current_tool_use_id,
                    tool_name=self._current_tool_name,
                    tool_input=tool_input,
                )
            )
            self._current_tool_use_id = ""
            self._current_tool_name = ""
            self._current_tool_content = {}
        elif content_type == "AUDIO":
            await self._event_queue.put(SessionEvent(type=SessionEventType.TURN_COMPLETE))


class _InternalToolUseEvent:
    """Internal event for tool use requests (not a SessionEvent)."""

    def __init__(self, tool_use_id: str, tool_name: str, tool_input: dict[str, Any]) -> None:
        self.tool_use_id: str = tool_use_id
        self.tool_name: str = tool_name
        self.tool_input: dict[str, Any] = tool_input
